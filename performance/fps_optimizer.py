"""fps_optimizer.py — 4.0"""
from __future__ import annotations
import time
import cv2
import numpy as np
from utils.config import UI_ACCENT2


class FPSOptimizer:
    def __init__(self, smoothing=0.92):
        self._s   = smoothing
        self._fps = 0.0
        self._pt  = time.perf_counter()

    def tick(self) -> float:
        now = time.perf_counter()
        dt  = max(now - self._pt, 1e-6)
        self._pt  = now
        self._fps = self._s*self._fps + (1-self._s)*(1.0/dt)
        return self._fps

    def draw(self, frame: np.ndarray):
        t = f"FPS {self._fps:.0f}"
        cv2.putText(frame,t,(12,32),cv2.FONT_HERSHEY_SIMPLEX,0.58,(0,0,0),3,cv2.LINE_AA)
        cv2.putText(frame,t,(12,32),cv2.FONT_HERSHEY_SIMPLEX,0.58,UI_ACCENT2,1,cv2.LINE_AA)

    @property
    def fps(self): return self._fps
