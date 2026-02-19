"""
multi_hand_detector.py
----------------------
Dual-hand detection using MediaPipe 0.10+ Tasks API.

Returns up to 2 hands. Each hand result includes:
  • norm_landmarks  : list of 21 (x, y, z) normalised tuples
  • pixel_landmarks : list of 21 (px, py) at display resolution
  • handedness      : "Left" or "Right"

Hand assignment:
  • Primary hand   (index 0) → drawing
  • Secondary hand (index 1) → tool / gesture commands
"""

from __future__ import annotations

import os
import time
import urllib.request
import cv2
import numpy as np
from typing import Optional

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import (
    HandLandmarker, HandLandmarkerOptions, RunningMode
)

from utils.config import (
    MAX_NUM_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE,
    MODEL_URL, MODEL_FILENAME, INDEX_TIP,
    DISPLAY_WIDTH, DISPLAY_HEIGHT, DETECT_WIDTH, DETECT_HEIGHT,
)

_MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_FILENAME)

_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]


def _ensure_model() -> str:
    if not os.path.exists(_MODEL_PATH):
        print("[INFO] Downloading hand landmarker model (~9 MB) …")
        urllib.request.urlretrieve(MODEL_URL, _MODEL_PATH)
        print(f"[INFO] Model → {_MODEL_PATH}")
    return _MODEL_PATH


def _draw_hand(frame: np.ndarray, pixel_lm: list, color: tuple = (0, 190, 90)) -> None:
    for a, b in _CONNECTIONS:
        cv2.line(frame, pixel_lm[a], pixel_lm[b], color, 1, cv2.LINE_AA)
    for pt in pixel_lm:
        cv2.circle(frame, pt, 3, (255, 255, 255), cv2.FILLED)
        cv2.circle(frame, pt, 3, color, 1)


class HandResult:
    """Holds processed result for one detected hand."""
    __slots__ = ("norm_lm", "pixel_lm", "handedness", "index_tip")

    def __init__(self, norm_lm, pixel_lm, handedness="Right"):
        self.norm_lm    = norm_lm
        self.pixel_lm   = pixel_lm
        self.handedness = handedness
        self.index_tip  = pixel_lm[INDEX_TIP]


class MultiHandDetector:
    """
    Detects up to 2 hands. Returns list of HandResult (0–2 items).

    Usage
    -----
    detector = MultiHandDetector()
    hands = detector.process(frame)     # list[HandResult]
    detector.draw_landmarks(frame, hands)
    detector.release()
    """

    def __init__(self) -> None:
        model_path = _ensure_model()
        options = HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=MAX_NUM_HANDS,
            min_hand_detection_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._last_hands: list[HandResult] = []
        self._last_ts_ms = 0

    def process(self, frame: np.ndarray) -> list[HandResult]:
        orig_h, orig_w = frame.shape[:2]
        if (orig_w, orig_h) != (DETECT_WIDTH, DETECT_HEIGHT):
            small = cv2.resize(frame, (DETECT_WIDTH, DETECT_HEIGHT))
        else:
            small = frame
        rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int(time.monotonic() * 1000)
        if ts_ms <= self._last_ts_ms:
            ts_ms = self._last_ts_ms + 1
        self._last_ts_ms = ts_ms
        result = self._landmarker.detect_for_video(mp_img, ts_ms)

        hands: list[HandResult] = []
        if not result.hand_landmarks:
            self._last_hands = hands
            return hands

        for i, hand_lm in enumerate(result.hand_landmarks):
            handedness = "Right"
            if result.handedness and i < len(result.handedness):
                handedness = result.handedness[i][0].display_name

            norm_lm  = [(lm.x, lm.y, lm.z) for lm in hand_lm]
            pixel_lm = [(int(lm.x * orig_w), int(lm.y * orig_h)) for lm in hand_lm]
            hands.append(HandResult(norm_lm, pixel_lm, handedness))

        self._last_hands = hands
        return hands

    def draw_landmarks(self, frame: np.ndarray, hands: list[HandResult]) -> None:
        colors = [(0, 200, 100), (100, 100, 255)]
        for i, h in enumerate(hands):
            _draw_hand(frame, h.pixel_lm, colors[i % 2])
            # Label hand
            tip = h.index_tip
            cv2.putText(frame, f"H{i+1}:{h.handedness[0]}",
                        (tip[0] + 8, tip[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                        colors[i % 2], 1, cv2.LINE_AA)

    def release(self) -> None:
        self._landmarker.close()
