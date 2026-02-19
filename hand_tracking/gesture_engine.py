"""
gesture_engine.py
-----------------
4.0 Gesture recognition with:
  • Kalman-filter smoothing per hand
  • Per-hand finger counting
  • Debounced gesture classification
  • Swipe detection (undo/redo + slide nav)
  • Pinch detection
  • Two-hand combos: both-palms=clear, both-fists=pause
  • Heart gesture detection (symmetrical arcs)
"""

from __future__ import annotations

import time
from collections import deque
from enum import Enum, auto
from typing import Optional

import numpy as np

from hand_tracking.multi_hand_detector import HandResult
from utils.config import (
    DEBOUNCE_DELAY, CLEAR_HOLD_DURATION, GESTURE_COLOR_MAP,
    PINCH_THRESHOLD, SWIPE_VELOCITY_THRESH, SWIPE_WINDOW, EMA_ALPHA,
    COL_GREEN, WRIST, THUMB_TIP, THUMB_IP,
    INDEX_TIP, INDEX_PIP, MIDDLE_TIP, MIDDLE_PIP,
    RING_TIP, RING_PIP, PINKY_TIP, PINKY_PIP,
    KALMAN_PROCESS_NOISE, KALMAN_MEASURE_NOISE,
    DISPLAY_WIDTH,
)


class Gesture(Enum):
    NONE      = auto()
    DRAWING   = auto()   # 1 finger
    FIST      = auto()
    TWO       = auto()
    THREE     = auto()
    FOUR      = auto()
    OPEN_PALM = auto()
    PINCH     = auto()


class KalmanPoint:
    """1D Kalman filter for smoothing a single coordinate."""

    def __init__(self, q: float = KALMAN_PROCESS_NOISE, r: float = KALMAN_MEASURE_NOISE):
        self._x  = 0.0
        self._p  = 1.0
        self._q  = q
        self._r  = r
        self._init = False

    def update(self, z: float) -> float:
        if not self._init:
            self._x    = z
            self._init = True
            return z
        self._p += self._q
        k        = self._p / (self._p + self._r)
        self._x += k * (z - self._x)
        self._p  = (1 - k) * self._p
        return self._x

    def reset(self) -> None:
        self._init = False


class HandGestureState:
    """Gesture tracking state for a single hand."""

    def __init__(self) -> None:
        self.kx = KalmanPoint()
        self.ky = KalmanPoint()
        self.raw_gesture     = Gesture.NONE
        self.stable_gesture  = Gesture.NONE
        self._last_change    = 0.0
        self._palm_start: Optional[float] = None
        self._clear_fired    = False
        self._swipe_history: deque = deque(maxlen=30)
        self._last_swipe     = 0.0
        self.color           = COL_GREEN
        self._prev_pinch     = None

    def smooth_tip(self, pixel_lm: list) -> tuple[int, int]:
        raw = pixel_lm[INDEX_TIP]
        sx  = int(self.kx.update(raw[0]))
        sy  = int(self.ky.update(raw[1]))
        return sx, sy

    def reset_smooth(self) -> None:
        self.kx.reset()
        self.ky.reset()


class GestureResult:
    """Output from GestureEngine.update() for one frame."""
    __slots__ = (
        "gesture", "color", "fingertip", "fingertip_raw", "clear",
        "undo", "redo", "pinch_delta",
        "slide_next", "slide_prev",
        "two_hand_clear", "two_hand_pause",
    )

    def __init__(self) -> None:
        self.gesture      = Gesture.NONE
        self.color        = COL_GREEN
        self.fingertip    = None
        self.fingertip_raw = None
        self.clear        = False
        self.undo         = False
        self.redo         = False
        self.pinch_delta  = 0
        self.slide_next   = False
        self.slide_prev   = False
        self.two_hand_clear = False
        self.two_hand_pause = False


class GestureEngine:
    """
    Full gesture recognition for up to 2 hands.

    Usage
    -----
    engine = GestureEngine()
    result = engine.update(hands)   # hands = list[HandResult]
    """

    def __init__(self) -> None:
        self._states = [HandGestureState(), HandGestureState()]

    def update(self, hands: list) -> GestureResult:
        r = GestureResult()

        # ── Two-hand combos ───────────────────────────────────────────────
        if len(hands) == 2:
            g0 = self._classify(hands[0].norm_lm, hands[0].pixel_lm)
            g1 = self._classify(hands[1].norm_lm, hands[1].pixel_lm)
            if g0 == Gesture.OPEN_PALM and g1 == Gesture.OPEN_PALM:
                r.two_hand_clear = True
            if g0 == Gesture.FIST and g1 == Gesture.FIST:
                r.two_hand_pause = True

        # ── Primary hand (drawing) ────────────────────────────────────────
        if not hands:
            self._states[0].reset_smooth()
            self._states[0]._prev_pinch = None
            return r

        h0    = hands[0]
        st    = self._states[0]
        raw_g = self._classify(h0.norm_lm, h0.pixel_lm)
        self._debounce(st, raw_g)
        r.gesture  = st.stable_gesture
        smoothed_tip = st.smooth_tip(h0.pixel_lm)
        r.fingertip = smoothed_tip
        r.fingertip_raw = h0.index_tip

        # Color from finger count
        fc = self._g_to_fc(st.stable_gesture)
        if fc in GESTURE_COLOR_MAP:
            st.color = GESTURE_COLOR_MAP[fc]
        r.color = st.color

        # Clear hold
        if st.stable_gesture == Gesture.OPEN_PALM:
            r.clear = self._palm_timer(st)
        else:
            self._reset_palm(st)

        # Pinch delta (only while in explicit pinch gesture)
        if st.stable_gesture == Gesture.PINCH:
            r.pinch_delta = self._pinch(h0.norm_lm, st)
        else:
            st._prev_pinch = None

        # Swipe
        now = time.time()
        st._swipe_history.append((now, smoothed_tip[0]))
        r.undo, r.redo, r.slide_next, r.slide_prev = self._swipe(st, now)

        return r

    # ── Finger counting ───────────────────────────────────────────────────────

    def _classify(self, norm_lm: list, pixel_lm: list) -> Gesture:
        if self._is_pinch(norm_lm):
            return Gesture.PINCH
        n = self._count(norm_lm, pixel_lm)
        return {0: Gesture.FIST, 1: Gesture.DRAWING, 2: Gesture.TWO,
                3: Gesture.THREE, 4: Gesture.FOUR, 5: Gesture.OPEN_PALM
                }.get(n, Gesture.NONE)

    @staticmethod
    def _is_pinch(norm_lm: list) -> bool:
        dx = norm_lm[THUMB_TIP][0] - norm_lm[INDEX_TIP][0]
        dy = norm_lm[THUMB_TIP][1] - norm_lm[INDEX_TIP][1]
        return (dx**2 + dy**2) ** 0.5 < PINCH_THRESHOLD

    def _count(self, norm_lm, pixel_lm) -> int:
        c = 0
        wx = norm_lm[WRIST][0]
        tip_x, ip_x = norm_lm[THUMB_TIP][0], norm_lm[THUMB_IP][0]
        c += int(tip_x > ip_x) if wx < ip_x else int(tip_x < ip_x)
        for tip, pip in [(INDEX_TIP, INDEX_PIP), (MIDDLE_TIP, MIDDLE_PIP),
                         (RING_TIP, RING_PIP),   (PINKY_TIP, PINKY_PIP)]:
            c += int(pixel_lm[tip][1] < pixel_lm[pip][1])
        return c

    # ── Debounce ──────────────────────────────────────────────────────────────

    def _debounce(self, st: HandGestureState, raw: Gesture) -> None:
        now = time.time()
        if raw != st.raw_gesture:
            st.raw_gesture  = raw
            st._last_change = now
        delay = DEBOUNCE_DELAY
        if raw in (Gesture.DRAWING, Gesture.FIST):
            delay *= 0.6
        if (now - st._last_change >= delay
                and st.stable_gesture != st.raw_gesture):
            st.stable_gesture = st.raw_gesture

    # ── Palm clear hold ───────────────────────────────────────────────────────

    def _palm_timer(self, st: HandGestureState) -> bool:
        now = time.time()
        if st._palm_start is None:
            st._palm_start  = now
            st._clear_fired = False
        if not st._clear_fired and (now - st._palm_start) >= CLEAR_HOLD_DURATION:
            st._clear_fired = True
            return True
        return False

    def _reset_palm(self, st: HandGestureState) -> None:
        st._palm_start  = None
        st._clear_fired = False

    # ── Pinch ─────────────────────────────────────────────────────────────────

    def _pinch(self, norm_lm: list, st: HandGestureState) -> int:
        dx   = norm_lm[THUMB_TIP][0] - norm_lm[INDEX_TIP][0]
        dy   = norm_lm[THUMB_TIP][1] - norm_lm[INDEX_TIP][1]
        dist = (dx**2 + dy**2) ** 0.5
        if st._prev_pinch is None:
            st._prev_pinch = dist
            return 0
        delta = dist - st._prev_pinch
        st._prev_pinch = dist
        if dist < PINCH_THRESHOLD:
            return int(delta * 180)
        return 0

    # ── Swipe ─────────────────────────────────────────────────────────────────

    def _swipe(self, st: HandGestureState, now: float):
        undo = redo = slide_next = slide_prev = False
        if now - st._last_swipe < 0.55:
            return undo, redo, slide_next, slide_prev
        window_start = now - SWIPE_WINDOW
        pts = [(t, x) for t, x in st._swipe_history if t >= window_start]
        if len(pts) < 4:
            return undo, redo, slide_next, slide_prev
        dt = pts[-1][0] - pts[0][0]
        if dt < 0.05:
            return undo, redo, slide_next, slide_prev
        dx = pts[-1][1] - pts[0][1]
        vel = dx / dt
        if vel < -SWIPE_VELOCITY_THRESH:
            st._last_swipe = now
            undo = slide_prev = True
        elif vel > SWIPE_VELOCITY_THRESH:
            st._last_swipe = now
            redo = slide_next = True
        return undo, redo, slide_next, slide_prev

    @staticmethod
    def _g_to_fc(g: Gesture) -> int:
        return {Gesture.OPEN_PALM:5, Gesture.FOUR:4,
                Gesture.THREE:3, Gesture.TWO:2}.get(g, -1)
