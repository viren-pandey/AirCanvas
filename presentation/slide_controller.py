"""
slide_controller.py — 4.0
--------------------------
Presentation / slide mode controller.

Features
--------
• Load a folder of images as slides
• Navigate with swipe gestures or voice
• Laser pointer mode (open palm hold)
• Highlight mode (index finger point)
• Slide counter overlay
• Annotations per slide (drawing layer saved per slide)
"""

from __future__ import annotations

import os
import glob
from typing import Optional

import cv2
import numpy as np

from utils.config import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, SLIDE_DIR,
    SLIDE_EXTENSIONS, LASER_COLOR, LASER_RADIUS,
    UI_TEXT, UI_ACCENT, UI_PANEL, UI_MUTED,
)


class SlideController:
    """
    Manages a folder-based image slideshow.

    Usage
    -----
    ctrl = SlideController()
    ctrl.load_folder("my_slides/")
    frame = ctrl.render(base_frame, fingertip, laser_mode)
    ctrl.next() / ctrl.prev()
    """

    def __init__(self) -> None:
        self._slides:  list[np.ndarray] = []
        self._index:   int   = 0
        self._folder:  str   = ""
        self._loaded:  bool  = False
        self._laser:   bool  = False
        self._annotations: dict[int, np.ndarray] = {}  # per-slide canvas

    # ── Load ──────────────────────────────────────────────────────────────────

    def load_folder(self, folder: str) -> int:
        """Load all images from folder. Returns count."""
        self._slides = []
        self._folder = folder
        if not os.path.isdir(folder):
            print(f"[SLIDES] Folder not found: {folder}")
            return 0

        paths = []
        for ext in SLIDE_EXTENSIONS:
            paths += glob.glob(os.path.join(folder, f"*{ext}"))
            paths += glob.glob(os.path.join(folder, f"*{ext.upper()}"))
        paths = sorted(set(paths))

        for p in paths:
            img = cv2.imread(p)
            if img is not None:
                img = cv2.resize(img, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
                self._slides.append(img)

        self._index  = 0
        self._loaded = len(self._slides) > 0
        print(f"[SLIDES] Loaded {len(self._slides)} slides from {folder}")
        return len(self._slides)

    def load_dialog(self) -> None:
        """Open folder picker in background thread."""
        import threading
        def _pick():
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw()
                root.attributes("-topmost", True)
                folder = filedialog.askdirectory(title="Select Slides Folder")
                root.destroy()
                if folder:
                    self.load_folder(folder)
            except Exception as e:
                print(f"[SLIDES] Dialog error: {e}")
        threading.Thread(target=_pick, daemon=True).start()

    # ── Navigation ────────────────────────────────────────────────────────────

    def next(self) -> None:
        if self._slides:
            self._index = (self._index + 1) % len(self._slides)

    def prev(self) -> None:
        if self._slides:
            self._index = (self._index - 1) % len(self._slides)

    def goto(self, n: int) -> None:
        if self._slides:
            self._index = max(0, min(n, len(self._slides) - 1))

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def count(self) -> int:
        return len(self._slides)

    @property
    def current_index(self) -> int:
        return self._index

    # ── Render ────────────────────────────────────────────────────────────────

    def render(
        self,
        base_frame:  np.ndarray,
        fingertip:   Optional[tuple],
        laser_mode:  bool,
    ) -> np.ndarray:
        """Render slide (or placeholder) with pointer and counter overlay."""
        if self._slides:
            frame = self._slides[self._index].copy()
        else:
            frame = self._placeholder()

        # Per-slide annotation layer
        if self._index in self._annotations:
            ann = self._annotations[self._index]
            b,g,r,a = cv2.split(ann)
            af  = a.astype(np.float32)/255.0
            for i,ch in enumerate([b,g,r]):
                frame[:,:,i] = (frame[:,:,i]*(1-af)+ch*af).astype(np.uint8)

        # Laser pointer
        if laser_mode and fingertip:
            self._draw_laser(frame, fingertip)

        # Slide counter
        self._draw_counter(frame)

        return frame

    def get_annotation_canvas(self) -> np.ndarray:
        """Return (or create) per-slide BGRA annotation canvas."""
        if self._index not in self._annotations:
            self._annotations[self._index] = np.zeros(
                (DISPLAY_HEIGHT, DISPLAY_WIDTH, 4), dtype=np.uint8
            )
        return self._annotations[self._index]

    def set_annotation_canvas(self, canvas: np.ndarray) -> None:
        self._annotations[self._index] = canvas

    # ── Internals ─────────────────────────────────────────────────────────────

    def _draw_laser(self, frame: np.ndarray, pt: tuple) -> None:
        x, y = pt
        # Outer glow
        for r, a in [(20, 40), (14, 80), (LASER_RADIUS, 160)]:
            overlay = frame.copy()
            cv2.circle(overlay, (x,y), r, LASER_COLOR, cv2.FILLED)
            cv2.addWeighted(overlay, a/255.0, frame, 1-a/255.0, 0, frame)
        cv2.circle(frame, (x,y), 4, (255,255,255), cv2.FILLED)

    def _draw_counter(self, frame: np.ndarray) -> None:
        if not self._slides:
            return
        text = f"  {self._index+1} / {len(self._slides)}  "
        font, scale = cv2.FONT_HERSHEY_SIMPLEX, 0.55
        (tw,th),_   = cv2.getTextSize(text, font, scale, 1)
        x = (DISPLAY_WIDTH - tw)//2
        y = DISPLAY_HEIGHT - 14
        cv2.rectangle(frame, (x-6,y-th-4),(x+tw+6,y+6), UI_PANEL, cv2.FILLED)
        cv2.putText(frame, text, (x,y), font, scale, UI_ACCENT, 1, cv2.LINE_AA)

    def _placeholder(self) -> np.ndarray:
        frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
        frame[:] = (18, 18, 24)
        lines = [
            "PRESENTATION MODE",
            "No slides loaded",
            "Say: 'Canvas, load slides'",
            "or press O to open folder",
        ]
        for i, line in enumerate(lines):
            font, scale = cv2.FONT_HERSHEY_SIMPLEX, 0.65 if i>0 else 0.9
            col = UI_ACCENT if i==0 else UI_MUTED
            (tw,th),_ = cv2.getTextSize(line, font, scale, 1)
            cv2.putText(frame, line,
                        ((DISPLAY_WIDTH-tw)//2, DISPLAY_HEIGHT//2-60+i*50),
                        font, scale, col, 1, cv2.LINE_AA)
        return frame
