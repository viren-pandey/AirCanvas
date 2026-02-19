from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


class BackendClientError(RuntimeError):
    """Raised when API calls fail."""


@dataclass(frozen=True)
class BackendClientConfig:
    base_url: str
    jwt_token: str
    timeout_sec: float = 8.0


class BackendClient:
    def __init__(self, config: BackendClientConfig) -> None:
        self._base_url = config.base_url.rstrip("/")
        self._token = config.jwt_token
        self._timeout = max(1.0, float(config.timeout_sec))

    @property
    def enabled(self) -> bool:
        return bool(self._base_url and self._token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.enabled:
            raise BackendClientError("Backend client is not configured")

        url = f"{self._base_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=self._headers(),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise BackendClientError(f"Network error calling {url}: {exc}") from exc

        if not response.ok:
            detail = response.text.strip()
            raise BackendClientError(f"{method} {url} failed [{response.status_code}] {detail}")

        try:
            return response.json()
        except ValueError as exc:
            raise BackendClientError(f"Invalid JSON response from {url}") from exc

    def start_session(self) -> str:
        payload = {
            "session_start": datetime.now(timezone.utc).isoformat(),
        }
        data = self._request("POST", "/api/v1/sessions", payload=payload)
        return str(data["id"])

    def end_session(self, session_id: str, avg_fps: float | None = None) -> None:
        payload: dict[str, Any] = {"session_end": datetime.now(timezone.utc).isoformat()}
        if avg_fps is not None:
            payload["avg_fps"] = float(avg_fps)
        self._request("PATCH", f"/api/v1/sessions/{session_id}/end", payload=payload)

    def request_upload_urls(
        self,
        session_id: str | None,
        brush_mode: str,
        shape_mode: str,
    ) -> dict[str, Any]:
        payload = {
            "session_id": session_id,
            "brush_mode": brush_mode,
            "shape_mode": shape_mode,
            "frame_extension": "png",
            "thumbnail_extension": "jpg",
        }
        return self._request("POST", "/api/v1/frames/upload-url", payload=payload)

    def complete_upload(self, frame_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/frames/{frame_id}/complete", payload={})

    def upload_bytes_to_signed_url(
        self,
        url: str,
        content: bytes,
        content_type: str,
    ) -> None:
        try:
            response = requests.put(
                url,
                data=content,
                headers={"Content-Type": content_type},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise BackendClientError(f"Signed URL upload failed: {exc}") from exc

        if response.status_code not in (200, 201):
            raise BackendClientError(
                f"Signed URL upload failed [{response.status_code}] {response.text[:200]}"
            )

