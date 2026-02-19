"""
overlays.py — 4.0
-----------------
All HUD overlay components:
  • StatusToast      — bottom-center notification
  • GestureHint      — gesture name flash
  • CursorGlow       — fingertip ring with draw pulse
  • VoiceHUD         — mic status + command toast + confidence
  • FadeTransition   — screen fade in/out
  • AnchorPulse      — shape anchor hold indicator
  • TwoHandIndicator — shows when dual-hand combo detected
"""

from __future__ import annotations

import math
import time
import cv2
import numpy as np
from typing import Optional

from utils.config import (
    UI_ACCENT, UI_ACCENT2, UI_HIGHLIGHT, UI_TEXT, UI_PANEL, UI_MUTED,
    UI_DANGER, TOOLBAR_H,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _shadow_text(frame, text, pos, font, scale, color, thick=1):
    x, y = pos
    cv2.putText(frame, text, (x+1,y+1), font, scale, (0,0,0), thick+1, cv2.LINE_AA)
    cv2.putText(frame, text, (x,  y  ), font, scale, color,   thick,   cv2.LINE_AA)


# ── Components ────────────────────────────────────────────────────────────────

class FadeTransition:
    def __init__(self, duration: float = 0.4):
        self._dur   = duration
        self._start = 0.0
        self._out   = True
        self._active = False

    def trigger(self):
        self._start  = time.time()
        self._active = True
        self._out    = True

    @property
    def active(self): return self._active

    def apply(self, frame: np.ndarray) -> np.ndarray:
        if not self._active: return frame
        t = (time.time()-self._start)/self._dur
        if self._out:
            alpha = min(t,1.0)
            if t>=1.0: self._out=False; self._start=time.time()
        else:
            alpha = max(1.0-t,0.0)
            if t>=1.0: self._active=False
        dark = np.zeros_like(frame)
        return cv2.addWeighted(dark, alpha, frame, 1-alpha, 0)


class StatusToast:
    def __init__(self):
        self._msg   = ""
        self._until = 0.0

    def show(self, msg: str, duration: float = 2.2):
        self._msg   = msg
        self._until = time.time() + duration

    def draw(self, frame: np.ndarray):
        if time.time() > self._until or not self._msg: return
        h,w = frame.shape[:2]
        font,scale,thick = cv2.FONT_HERSHEY_SIMPLEX, 0.60, 1
        (tw,th),_ = cv2.getTextSize(self._msg,font,scale,thick)
        x = (w-tw)//2; y = h-22
        cv2.rectangle(frame,(x-10,y-th-6),(x+tw+10,y+7),(16,16,24),cv2.FILLED)
        cv2.rectangle(frame,(x-10,y-th-6),(x+tw+10,y+7),UI_ACCENT,1)
        _shadow_text(frame,self._msg,(x,y),font,scale,UI_ACCENT2,thick)


class GestureHint:
    def __init__(self):
        self._text  = ""
        self._until = 0.0

    def show(self, text: str, dur: float = 1.0):
        self._text  = text
        self._until = time.time() + dur

    def draw(self, frame: np.ndarray):
        if not self._text or time.time()>self._until: return
        h,w = frame.shape[:2]
        font,scale = cv2.FONT_HERSHEY_SIMPLEX,0.70
        (tw,th),_  = cv2.getTextSize(self._text,font,scale,2)
        x = (w-tw)//2; y = TOOLBAR_H+46
        alpha = max(0.0, 1.0-(time.time()-(self._until-1.0))/1.0)
        col = tuple(int(c*alpha) for c in UI_HIGHLIGHT)
        _shadow_text(frame,self._text,(x,y),font,scale,col,2)


class CursorGlow:
    def draw(self, frame, pt, color, drawing: bool, eraser: bool):
        if pt is None: return
        x,y    = pt
        r_col  = (60,80,200) if eraser else color[:3]
        r_out  = 16 if drawing else 10
        r_in   = 5  if drawing else 3

        if drawing:
            # Animated outer pulse
            t     = time.time()
            pulse = int(r_out + 5*abs(math.sin(t*6)))
            cv2.circle(frame, (x, y), pulse, r_col, 1, cv2.LINE_AA)

        cv2.circle(frame,(x,y),r_out,r_col,1,cv2.LINE_AA)
        cv2.circle(frame,(x,y),r_in, r_col,cv2.FILLED,cv2.LINE_AA)


class VoiceHUD:
    def __init__(self):
        self._cmd_text  = ""
        self._cmd_until = 0.0

    def show_command(self, text: str, dur: float = 2.5):
        self._cmd_text  = f"MIC {text}"
        self._cmd_until = time.time() + dur

    def draw(self, frame, voice_active: bool, depth_blocked: bool):
        h,w = frame.shape[:2]

        # Mic badge (top-right)
        col = (40,200,80) if voice_active else (50,48,65)
        txt = "MIC ON" if voice_active else "MIC OFF"
        cv2.rectangle(frame,(w-78,8),(w-4,26),(14,14,20),cv2.FILLED)
        cv2.rectangle(frame,(w-78,8),(w-4,26),col,1)
        cv2.putText(frame,txt,(w-74,21),cv2.FONT_HERSHEY_SIMPLEX,0.38,col,1,cv2.LINE_AA)

        # Depth blocked
        if depth_blocked:
            txt2 = "DEPTH STOP"
            (tw,_),_ = cv2.getTextSize(txt2,cv2.FONT_HERSHEY_SIMPLEX,0.50,1)
            cv2.putText(frame,txt2,(w-tw-8,44),
                        cv2.FONT_HERSHEY_SIMPLEX,0.50,UI_DANGER,1,cv2.LINE_AA)

        # Command toast (right side)
        if self._cmd_text and time.time()<self._cmd_until:
            font,scale = cv2.FONT_HERSHEY_SIMPLEX,0.50
            (tw,th),_  = cv2.getTextSize(self._cmd_text,font,scale,1)
            x = w-tw-14; y = 64
            cv2.rectangle(frame,(x-6,y-th-4),(x+tw+6,y+5),(18,18,28),cv2.FILLED)
            cv2.rectangle(frame,(x-6,y-th-4),(x+tw+6,y+5),(40,200,80),1)
            cv2.putText(frame,self._cmd_text,(x,y),font,scale,(40,220,100),1,cv2.LINE_AA)


class AnchorPulse:
    """Animated ring showing hold progress for shape anchor."""

    def draw(self, frame, pt, progress: float):
        if pt is None or progress <= 0: return
        x,y = pt
        r   = 22
        # Background ring
        cv2.circle(frame,(x,y),r,(40,38,55),2,cv2.LINE_AA)
        # Progress arc
        start = -90
        end   = start + int(progress*360)
        steps = max(2, int(progress*36))
        pts   = []
        for i in range(steps+1):
            angle = math.radians(start+(end-start)*i/steps)
            pts.append((int(x+r*math.cos(angle)),int(y+r*math.sin(angle))))
        for i in range(len(pts)-1):
            cv2.line(frame,pts[i],pts[i+1],UI_HIGHLIGHT,2,cv2.LINE_AA)
        # Centre dot
        cv2.circle(frame,(x,y),4,UI_HIGHLIGHT if progress>=1.0 else UI_ACCENT,cv2.FILLED)


class TwoHandIndicator:
    """Brief overlay when dual-hand combo fires."""

    def __init__(self):
        self._text  = ""
        self._until = 0.0

    def show(self, text: str):
        self._text  = text
        self._until = time.time() + 1.5

    def draw(self, frame):
        if not self._text or time.time()>self._until: return
        h,w   = frame.shape[:2]
        font,scale = cv2.FONT_HERSHEY_SIMPLEX,0.80
        (tw,th),_  = cv2.getTextSize(self._text,font,scale,2)
        x = (w-tw)//2; y = h//2
        cv2.rectangle(frame,(x-16,y-th-10),(x+tw+16,y+14),(20,18,32),cv2.FILLED)
        cv2.rectangle(frame,(x-16,y-th-10),(x+tw+16,y+14),UI_HIGHLIGHT,1)
        _shadow_text(frame,self._text,(x,y),font,scale,UI_HIGHLIGHT,2)


class FPSDisplay:
    def __init__(self, smoothing=0.92):
        import time as _time
        self._s   = smoothing
        self._fps = 0.0
        self._pt  = _time.perf_counter()

    def tick(self) -> float:
        import time as _time
        now = _time.perf_counter()
        dt  = now - self._pt; self._pt = now
        if dt>0:
            raw      = 1.0/dt
            self._fps = self._s*self._fps + (1-self._s)*raw
        return self._fps

    def draw(self, frame):
        text = f"FPS {self._fps:.0f}"
        cv2.putText(frame,text,(12,32),cv2.FONT_HERSHEY_SIMPLEX,0.60,(0,0,0),3,cv2.LINE_AA)
        cv2.putText(frame,text,(12,32),cv2.FONT_HERSHEY_SIMPLEX,0.60,UI_ACCENT2,1,cv2.LINE_AA)
