"""
thread_manager.py — 4.0
-----------------------
Manages background threads for hand detection.
Detection runs at full speed; main loop reads latest cached result.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional
import numpy as np


class DetectionThread:
    """
    Background detection thread.

    put_frame() — push new frame (non-blocking)
    get_result() — read latest result (non-blocking)
    """

    def __init__(self, detect_fn: Callable) -> None:
        self._fn      = detect_fn
        self._frame:  Optional[np.ndarray] = None
        self._result: Any = []
        self._fl      = threading.Lock()
        self._rl      = threading.Lock()
        self._running = False
        self._event   = threading.Event()
        self._thread  = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._event.set()
        self._thread.join(timeout=2.0)

    def put_frame(self, frame: np.ndarray) -> None:
        with self._fl:
            self._frame = frame
        self._event.set()

    def get_result(self) -> Any:
        with self._rl:
            return self._result

    def _loop(self) -> None:
        while self._running:
            self._event.wait(timeout=0.1)
            self._event.clear()
            if not self._running:
                break
            with self._fl:
                frame = self._frame
            if frame is None:
                continue
            try:
                result = self._fn(frame)
            except Exception:
                result = []
            with self._rl:
                self._result = result
