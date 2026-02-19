"""
advanced_brush.py
-----------------
4.0 Advanced brush with:
  • Kalman-filtered coordinate smoothing
  • Dynamic thickness based on drawing speed
  • Eraser mode
  • Snap-to-grid support
"""

from __future__ import annotations

import time
from typing import Optional

from hand_tracking.gesture_engine import KalmanPoint
from utils.config import (
    DEFAULT_THICKNESS, MIN_THICKNESS, MAX_THICKNESS,
    ERASER_THICKNESS, SPEED_BRUSH_ENABLED,
    SPEED_MIN_FACTOR, SPEED_MAX_FACTOR,
    GRID_CELL_SIZE, SNAP_THRESHOLD,
)


class AdvancedBrush:
    """
    Manages brush state with speed-adaptive thickness and Kalman smoothing.

    Usage
    -----
    brush = AdvancedBrush()
    pt    = brush.smooth(raw_point)
    color, thick = brush.draw_params(base_color)
    """

    def __init__(self) -> None:
        self._thickness  = DEFAULT_THICKNESS
        self._eraser     = False
        self._kx         = KalmanPoint()
        self._ky         = KalmanPoint()
        self._prev_pt:   Optional[tuple] = None
        self._prev_time: float = 0.0
        self._speed:     float = 0.0
        self._snap_grid: bool  = False

    # ── Smoothing ─────────────────────────────────────────────────────────────

    def smooth(self, pt: Optional[tuple]) -> Optional[tuple]:
        if pt is None:
            self._kx.reset()
            self._ky.reset()
            self._prev_pt = None
            return None

        sx = int(self._kx.update(pt[0]))
        sy = int(self._ky.update(pt[1]))

        # Update speed estimate
        now = time.perf_counter()
        if self._prev_pt is not None:
            dx = sx - self._prev_pt[0]
            dy = sy - self._prev_pt[1]
            dt = max(now - self._prev_time, 1e-6)
            self._speed = ((dx**2 + dy**2) ** 0.5) / dt

        self._prev_pt   = (sx, sy)
        self._prev_time = now

        if self._snap_grid:
            sx = round(sx / GRID_CELL_SIZE) * GRID_CELL_SIZE
            sy = round(sy / GRID_CELL_SIZE) * GRID_CELL_SIZE

        return sx, sy

    def reset(self) -> None:
        self._kx.reset()
        self._ky.reset()
        self._prev_pt = None
        self._speed   = 0.0

    # ── Draw params ───────────────────────────────────────────────────────────

    def draw_params(self, base_color: tuple) -> tuple[tuple, int]:
        if self._eraser:
            return (0, 0, 0), ERASER_THICKNESS

        thick = self._thickness
        if SPEED_BRUSH_ENABLED and self._speed > 0:
            # Fast strokes → thinner, slow strokes → thicker
            norm_speed = min(self._speed / 800.0, 1.0)
            factor = SPEED_MAX_FACTOR - norm_speed * (SPEED_MAX_FACTOR - SPEED_MIN_FACTOR)
            thick  = max(MIN_THICKNESS, min(int(self._thickness * factor), MAX_THICKNESS))

        return base_color, thick

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def eraser(self) -> bool:
        return self._eraser

    @eraser.setter
    def eraser(self, val: bool) -> None:
        self._eraser = val
        self.reset()

    @property
    def thickness(self) -> int:
        return self._thickness

    def set_thickness(self, v: int) -> None:
        self._thickness = max(MIN_THICKNESS, min(int(v), MAX_THICKNESS))

    def adjust(self, delta: int) -> None:
        self.set_thickness(self._thickness + delta)

    @property
    def snap_grid(self) -> bool:
        return self._snap_grid

    @snap_grid.setter
    def snap_grid(self, val: bool) -> None:
        self._snap_grid = val
