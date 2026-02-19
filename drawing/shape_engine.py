"""
shape_engine.py
---------------
4.0 Shape drawing state machine.

Shapes: rectangle | circle | ellipse | triangle | line | heart

Flow:
  1. User selects shape (toolbar / voice)
  2. Hold index finger still for SHAPE_HOLD_SECONDS -> anchor locked (visual pulse)
  3. Drag to second point (live anti-aliased preview)
  4. Finalize via controller-triggered event (pinch release / stop / fist)
"""

from __future__ import annotations

import time
from typing import Optional
from utils.config import (
    SHAPE_EMA_ALPHA,
    SHAPE_HOLD_SECONDS,
    SHAPE_MIN_MOVE_PX,
    SHAPE_MIN_SIZE_PX,
    SHAPE_STILL_RADIUS_PX,
)


class ShapeEngine:

    IDLE      = "idle"
    ANCHORING = "anchoring"
    DRAGGING  = "dragging"

    SHAPES = ["rectangle", "circle", "ellipse", "line", "triangle", "heart"]

    def __init__(self) -> None:
        self.state        = self.IDLE
        self.active_shape = "rectangle"
        self.anchor:   Optional[tuple] = None
        self.current:  Optional[tuple] = None
        self._hold_start:    Optional[float] = None
        self._anchor_cand:   Optional[tuple] = None
        self._still_r = SHAPE_STILL_RADIUS_PX
        self._min_move_px = SHAPE_MIN_MOVE_PX
        self._min_size_px = SHAPE_MIN_SIZE_PX
        self._ema_tip: Optional[tuple[float, float]] = None

    def update(
        self,
        fingertip:      Optional[tuple],
        drawing_active: bool,
    ) -> None:
        """
        Update shape anchor/preview. Finalization is explicit via finalize().
        """
        stable_tip = self._smooth_tip(fingertip)

        if self.state == self.IDLE:
            if not drawing_active or stable_tip is None:
                return
            self._hold_start  = time.time()
            self._anchor_cand = stable_tip
            self.state        = self.ANCHORING
            return

        if self.state == self.ANCHORING:
            if not drawing_active or stable_tip is None:
                self._partial_reset()
                return
            dx = abs(stable_tip[0] - self._anchor_cand[0])
            dy = abs(stable_tip[1] - self._anchor_cand[1])
            if dx > self._still_r or dy > self._still_r:
                self._hold_start  = time.time()
                self._anchor_cand = stable_tip
                return
            if time.time() - self._hold_start >= SHAPE_HOLD_SECONDS:
                self.anchor  = self._anchor_cand
                self.current = self._anchor_cand
                self.state   = self.DRAGGING
            return

        if self.state == self.DRAGGING:
            if drawing_active and stable_tip is not None:
                if self.current is None:
                    self.current = stable_tip
                elif self._dist(self.current, stable_tip) >= self._min_move_px:
                    # Ignore micro-jitter to keep preview geometry stable.
                    self.current = stable_tip

    def finalize(self) -> Optional[tuple]:
        """Commit current preview geometry if valid."""
        if not self.is_dragging or self.anchor is None or self.current is None:
            return None
        if not self._is_valid_shape(self.anchor, self.current):
            self._full_reset()
            return None
        result = (self.active_shape, self.anchor, self.current)
        self._full_reset()
        return result

    def cancel(self):
        self._full_reset()

    def set_shape(self, shape: str):
        if shape in self.SHAPES:
            self.active_shape = shape
            self._full_reset()

    @property
    def is_dragging(self) -> bool:
        return self.state == self.DRAGGING

    @property
    def has_preview(self) -> bool:
        return self.is_dragging and self.anchor is not None and self.current is not None

    @property
    def hold_progress(self) -> float:
        """0-1 progress through hold timer (for anchor animation)."""
        if self.state != self.ANCHORING or self._hold_start is None:
            return 0.0
        return min(1.0, (time.time() - self._hold_start) / SHAPE_HOLD_SECONDS)

    def _partial_reset(self):
        self.state       = self.IDLE
        self._hold_start = None
        self._anchor_cand = None
        self._ema_tip    = None

    def _full_reset(self):
        self.state        = self.IDLE
        self.anchor       = None
        self.current      = None
        self._hold_start  = None
        self._anchor_cand = None
        self._ema_tip     = None

    def _smooth_tip(self, fingertip: Optional[tuple]) -> Optional[tuple]:
        if fingertip is None:
            self._ema_tip = None
            return None
        x, y = float(fingertip[0]), float(fingertip[1])
        if self._ema_tip is None:
            self._ema_tip = (x, y)
        else:
            ex, ey = self._ema_tip
            a = SHAPE_EMA_ALPHA
            self._ema_tip = (ex + a * (x - ex), ey + a * (y - ey))
        sx, sy = self._ema_tip
        return int(round(sx)), int(round(sy))

    @staticmethod
    def _dist(p1: tuple, p2: tuple) -> float:
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return (dx * dx + dy * dy) ** 0.5

    def _is_valid_shape(self, p1: tuple, p2: tuple) -> bool:
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if self.active_shape == "line":
            return (dx * dx + dy * dy) ** 0.5 >= self._min_size_px
        return max(dx, dy) >= self._min_size_px
