"""
onboarding.py — 4.0
--------------------
Minimal dark onboarding:
  Screen 1: Gesture reference card (press SPACE/ENTER to continue)
  Screen 2: Name entry
"""

from __future__ import annotations

import time
import cv2
import numpy as np

from utils.config import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT,
    UI_ACCENT, UI_ACCENT2, UI_TEXT, UI_MUTED, UI_PANEL, UI_HIGHLIGHT,
    COL_GREEN, COL_RED, COL_BLUE, COL_BLACK,
)


def _glass(frame, x1,y1,x2,y2, alpha=0.82, fill=(18,18,26), border=None):
    ov = frame.copy()
    cv2.rectangle(ov,(x1,y1),(x2,y2),fill,cv2.FILLED)
    cv2.addWeighted(ov,alpha,frame,1-alpha,0,frame)
    cv2.rectangle(frame,(x1,y1),(x2,y2),border or UI_ACCENT,1)


def _center(frame, text, y, scale=0.7, color=None, thick=1):
    color = color or UI_TEXT
    font  = cv2.FONT_HERSHEY_SIMPLEX
    (tw,_),_ = cv2.getTextSize(text,font,scale,thick)
    x = (DISPLAY_WIDTH-tw)//2
    cv2.putText(frame,text,(x+1,y+1),font,scale,(0,0,0),thick+1,cv2.LINE_AA)
    cv2.putText(frame,text,(x,  y  ),font,scale,color,  thick,  cv2.LINE_AA)


class OnboardingScreen:

    GESTURES = [
        ("1 Finger",    "Draw freely",                COL_GREEN),
        ("Fist",        "Pause / stop drawing",        UI_MUTED),
        ("2 Fingers",   "Colour: Black",               COL_BLACK),
        ("3 Fingers",   "Colour: Blue",                COL_BLUE),
        ("4 Fingers",   "Colour: Red",                 COL_RED),
        ("5 Fingers",   "Colour: Green  /  hold=Clear",COL_GREEN),
        ("Pinch",       "Resize brush",                UI_ACCENT),
        ("Swipe ←",     "Undo / Prev slide",           UI_HIGHLIGHT),
        ("Swipe →",     "Redo / Next slide",           UI_HIGHLIGHT),
        ("2 Palms",     "Clear canvas",                UI_ACCENT2),
        ("2 Fists",     "Pause system",                UI_MUTED),
        ("Palm hold",   "Laser pointer (slide mode)",  (0,60,255)),
    ]

    def __init__(self):
        self._screen = 0
        self._name   = ""
        self._done   = False
        self._fade   = 0.0

    def update(self, frame: np.ndarray, key: int):
        if self._done:
            return True, self._name
        self._fade = min(1.0, self._fade+0.05)

        # Dark base
        dark = np.zeros_like(frame)
        cv2.addWeighted(dark,0.60,frame,0.40,0,frame)

        if self._screen == 0:
            self._draw_ref(frame)
            if key in (13,32,ord('n'),ord('N')):
                self._screen = 1; self._fade = 0.0
        else:
            self._draw_name(frame, key)

        return False, ""

    def _draw_ref(self, frame):
        W,H = DISPLAY_WIDTH,DISPLAY_HEIGHT
        pw,ph = 660,460
        px,py = (W-pw)//2, (H-ph)//2
        _glass(frame,px,py,px+pw,py+ph)

        _center(frame,"✋  AirCanvas 4.0  —  Gesture Reference",
                py+38, scale=0.75, color=UI_ACCENT, thick=1)
        cv2.line(frame,(px+20,py+52),(px+pw-20,py+52),(40,38,55),1)

        rh = 32
        for i,(gesture,desc,col) in enumerate(self.GESTURES):
            ry = py+68+i*rh
            cv2.putText(frame, gesture,(px+22,ry),cv2.FONT_HERSHEY_SIMPLEX,0.44,col,1,cv2.LINE_AA)
            cv2.putText(frame, f"→  {desc}",(px+200,ry),cv2.FONT_HERSHEY_SIMPLEX,0.42,UI_TEXT,1,cv2.LINE_AA)

        pulse = int(160+80*abs(np.sin(time.time()*2.5)))
        _center(frame,"Press  SPACE  to continue",
                py+ph-18,scale=0.46,color=(pulse,pulse,pulse))

    def _draw_name(self, frame, key: int):
        if key==13:
            self._done = True
            if not self._name: self._name = "Artist"
            return
        elif key==8 and self._name:
            self._name = self._name[:-1]
        elif 32<=key<=126 and len(self._name)<22:
            self._name += chr(key)

        W,H = DISPLAY_WIDTH,DISPLAY_HEIGHT
        pw,ph = 480,200
        px,py = (W-pw)//2,(H-ph)//2
        _glass(frame,px,py,px+pw,py+ph)
        _center(frame,"Who's painting today?",py+44,scale=0.65,color=UI_ACCENT)

        bx1,by1,bx2,by2 = px+36,py+70,px+pw-36,py+118
        cv2.rectangle(frame,(bx1,by1),(bx2,by2),(22,22,30),cv2.FILLED)
        cv2.rectangle(frame,(bx1,by1),(bx2,by2),UI_ACCENT,1)
        cursor = "|" if int(time.time()*2)%2==0 else " "
        cv2.putText(frame,self._name+cursor,(bx1+10,by2-14),
                    cv2.FONT_HERSHEY_SIMPLEX,0.62,UI_TEXT,1,cv2.LINE_AA)
        _center(frame,"Press  ENTER  to start",py+ph-18,scale=0.44,color=UI_MUTED)
