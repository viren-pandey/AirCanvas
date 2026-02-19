from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np

from utils.config import (
    AIRCANVAS_API_BASE_URL,
    AIRCANVAS_API_TIMEOUT_SEC,
    AIRCANVAS_JWT_TOKEN,
    AUTO_CAPTURE_DEFAULT_ENABLED,
    AUTO_CAPTURE_INTERVAL_SEC,
    FRAME_UPLOAD_FALLBACK_DIR,
    FRAME_UPLOAD_LOCAL_FALLBACK,
    FRAME_PNG_COMPRESSION,
    FRAME_THUMB_JPEG_QUALITY,
    FRAME_THUMB_MAX_WIDTH,
    FRAME_UPLOAD_QUEUE_SIZE,
    FRAME_UPLOAD_RETRY_BACKOFF_SEC,
    FRAME_UPLOAD_RETRY_MAX,
)
from services.backend_client import BackendClient, BackendClientConfig, BackendClientError


@dataclass
class _FrameJob:
    frame: np.ndarray
    brush_mode: str
    shape_mode: str
    attempt: int = 0


class FrameUploader:
    """
    Asynchronous frame uploader.

    - Never blocks the drawing loop: enqueue is non-blocking.
    - Retries transient network errors.
    - Handles session lifecycle metadata.
    """

    def __init__(
        self,
        client: BackendClient,
        queue_size: int = FRAME_UPLOAD_QUEUE_SIZE,
        max_retries: int = FRAME_UPLOAD_RETRY_MAX,
        retry_backoff_sec: float = FRAME_UPLOAD_RETRY_BACKOFF_SEC,
        local_fallback_enabled: bool = FRAME_UPLOAD_LOCAL_FALLBACK,
        fallback_dir: str = FRAME_UPLOAD_FALLBACK_DIR,
    ) -> None:
        self._client = client
        self._queue: queue.Queue[_FrameJob] = queue.Queue(maxsize=max(2, int(queue_size)))
        self._max_retries = max(0, int(max_retries))
        self._retry_backoff = max(0.1, float(retry_backoff_sec))
        self._local_fallback_enabled = bool(local_fallback_enabled)
        self._fallback_dir = fallback_dir.strip() or "saves"

        self._running = False
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._session_id: str | None = None
        self._lock = threading.Lock()

        self.auto_capture_enabled = AUTO_CAPTURE_DEFAULT_ENABLED
        self.auto_capture_interval_sec = AUTO_CAPTURE_INTERVAL_SEC
        self._last_auto_capture_ts = 0.0

    @classmethod
    def from_env(cls) -> FrameUploader | None:
        base_url = AIRCANVAS_API_BASE_URL
        jwt_token = AIRCANVAS_JWT_TOKEN
        if not base_url or not jwt_token:
            return None

        client = BackendClient(
            BackendClientConfig(
                base_url=base_url,
                jwt_token=jwt_token,
                timeout_sec=float(AIRCANVAS_API_TIMEOUT_SEC),
            )
        )
        return cls(client)

    @property
    def enabled(self) -> bool:
        return self._client.enabled

    def start(self) -> None:
        if not self.enabled or self._running:
            return
        self._running = True
        self._worker.start()

    def stop(self, avg_fps: float | None = None, flush_timeout_sec: float = 4.0) -> None:
        if not self._running:
            return

        end_at = time.time() + max(0.5, float(flush_timeout_sec))
        while time.time() < end_at and not self._queue.empty():
            time.sleep(0.05)

        self._running = False
        self._worker.join(timeout=2.0)

        session_id = self._session_id
        if session_id:
            try:
                self._client.end_session(session_id=session_id, avg_fps=avg_fps)
            except BackendClientError as exc:
                print(f"[UPLOAD] Failed to close session: {exc}")

    def enqueue_frame(self, frame: np.ndarray, brush_mode: str, shape_mode: str) -> bool:
        if not self.enabled:
            return False
        job = _FrameJob(frame=frame.copy(), brush_mode=brush_mode, shape_mode=shape_mode)
        try:
            self._queue.put_nowait(job)
            return True
        except queue.Full:
            return False

    def should_auto_capture_now(self) -> bool:
        if not self.auto_capture_enabled:
            return False
        now = time.time()
        interval = max(1.0, float(self.auto_capture_interval_sec))
        if now - self._last_auto_capture_ts < interval:
            return False
        self._last_auto_capture_ts = now
        return True

    def toggle_auto_capture(self) -> bool:
        self.auto_capture_enabled = not self.auto_capture_enabled
        return self.auto_capture_enabled

    def set_auto_capture_interval(self, seconds: float) -> None:
        self.auto_capture_interval_sec = max(1.0, float(seconds))

    def queue_size(self) -> int:
        return self._queue.qsize()

    def _run(self) -> None:
        self._ensure_session()
        while self._running or not self._queue.empty():
            try:
                job = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                self._upload_job(job)
            except Exception as exc:
                if job.attempt < self._max_retries and self._running:
                    job.attempt += 1
                    time.sleep(self._retry_backoff * (2 ** (job.attempt - 1)))
                    try:
                        self._queue.put_nowait(job)
                    except queue.Full:
                        print("[UPLOAD] Queue full; dropping retried frame.")
                else:
                    print(f"[UPLOAD] Dropped frame after retries: {exc}")
                    self._save_local_fallback(job)
            finally:
                self._queue.task_done()

    def _ensure_session(self) -> None:
        if self._session_id or not self.enabled:
            return
        try:
            session_id = self._client.start_session()
            with self._lock:
                self._session_id = session_id
            print(f"[UPLOAD] Session started: {session_id}")
        except BackendClientError as exc:
            print(f"[UPLOAD] Could not start remote session yet: {exc}")

    def _upload_job(self, job: _FrameJob) -> None:
        if not self._session_id:
            self._ensure_session()

        payload = self._client.request_upload_urls(
            session_id=self._session_id,
            brush_mode=job.brush_mode,
            shape_mode=job.shape_mode,
        )

        png_bytes = self._encode_png(job.frame)
        thumb_bytes = self._encode_thumbnail(job.frame)

        self._client.upload_bytes_to_signed_url(
            payload["frame_upload_url"],
            png_bytes,
            content_type="image/png",
        )
        self._client.upload_bytes_to_signed_url(
            payload["thumbnail_upload_url"],
            thumb_bytes,
            content_type="image/jpeg",
        )
        self._client.complete_upload(str(payload["frame_id"]))

    @staticmethod
    def _encode_png(frame: np.ndarray) -> bytes:
        ok, encoded = cv2.imencode(
            ".png",
            frame,
            [cv2.IMWRITE_PNG_COMPRESSION, int(FRAME_PNG_COMPRESSION)],
        )
        if not ok:
            raise RuntimeError("PNG encoding failed")
        return encoded.tobytes()

    @staticmethod
    def _encode_thumbnail(frame: np.ndarray) -> bytes:
        h, w = frame.shape[:2]
        if w <= 0 or h <= 0:
            raise RuntimeError("Invalid frame dimensions")

        max_width = int(FRAME_THUMB_MAX_WIDTH)
        if w > max_width:
            scale = max_width / float(w)
            target = (max_width, max(1, int(h * scale)))
            resized = cv2.resize(frame, target, interpolation=cv2.INTER_AREA)
        else:
            resized = frame

        ok, encoded = cv2.imencode(
            ".jpg",
            resized,
            [cv2.IMWRITE_JPEG_QUALITY, int(FRAME_THUMB_JPEG_QUALITY)],
        )
        if not ok:
            raise RuntimeError("Thumbnail encoding failed")
        return encoded.tobytes()

    def _save_local_fallback(self, job: _FrameJob) -> None:
        if not self._local_fallback_enabled:
            return
        try:
            os.makedirs(self._fallback_dir, exist_ok=True)
            epoch_ms = int(time.time() * 1000)
            path = os.path.join(self._fallback_dir, f"upload_fallback_{epoch_ms}.png")
            ok = cv2.imwrite(path, job.frame)
            if ok:
                print(
                    f"[UPLOAD] Saved local fallback frame -> {path} "
                    f"(brush={job.brush_mode}, shape={job.shape_mode})"
                )
            else:
                print("[UPLOAD] Local fallback save failed: cv2.imwrite returned False.")
        except Exception as exc:
            print(f"[UPLOAD] Local fallback save failed: {exc}")
