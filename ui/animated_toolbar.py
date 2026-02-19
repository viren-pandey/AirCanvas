"""
animated_toolbar.py — 4.0
--------------------------
Futuristic floating glassmorphism toolbar with:
  • Hover-to-activate (0.5 s dwell activates button)
  • Pulse animation on activate
  • Hover glow ring
  • Slide-in animation on first render
  • All 4.0 actions: colour, brush slider, shapes, tools, slides
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from utils.config import (
    DISPLAY_WIDTH, TOOLBAR_H, BTN_W, BTN_H, BTN_GAP,
    COL_GREEN, COL_RED, COL_BLUE, COL_BLACK, COL_YELLOW, COL_PURPLE, COL_ORANGE,
    MIN_THICKNESS, MAX_THICKNESS,
    HOVER_ACTIVATE_SEC,
    UI_BG, UI_PANEL, UI_BORDER, UI_ACCENT, UI_ACCENT2, UI_HIGHLIGHT,
    UI_TEXT, UI_MUTED, UI_DANGER,
)

# ── Minimal design tokens ──────────────────────────────────────────────────────
_BG_ALPHA   = 0.92
_PILL_IDLE  = (22, 22, 30)
_PILL_HOV   = (35, 32, 55)
_PILL_ACT   = (255, 255, 255)
_TEXT_IDLE  = (120, 118, 140)
_TEXT_ACT   = (14, 12, 20)
_SWATCH_R   = 8
_DIVIDER    = (40, 38, 55)


@dataclass
class _Btn:
    icon:    str
    action:  str
    color:   Optional[tuple] = None
    rect:    tuple = field(default_factory=tuple)
    _hover_start: float = field(default=0.0, repr=False)
    _pulse:       float = field(default=0.0, repr=False)

    def hover_progress(self) -> float:
        if self._hover_start == 0.0:
            return 0.0
        return min(1.0, (time.time() - self._hover_start) / HOVER_ACTIVATE_SEC)

    def start_hover(self) -> None:
        if self._hover_start == 0.0:
            self._hover_start = time.time()

    def end_hover(self) -> None:
        self._hover_start = 0.0

    def trigger_pulse(self) -> None:
        self._pulse = time.time()

    def pulse_alpha(self) -> float:
        age = time.time() - self._pulse
        if age > 0.5:
            return 0.0
        return max(0.0, 1.0 - age / 0.5)


class AnimatedToolbar:
    """
    Floating toolbar with hover-to-activate and pulse animations.

    Usage
    -----
    tb = AnimatedToolbar()
    tb.render(frame, active_action, active_color, thickness, slide_mode)
    action = tb.update_hover(fingertip)   # call every frame; returns action or None
    """

    _COLORS = [
        (COL_GREEN,  "color_green"),
        (COL_RED,    "color_red"),
        (COL_BLUE,   "color_blue"),
        (COL_BLACK,  "color_black"),
        (COL_YELLOW, "color_yellow"),
        (COL_PURPLE, "color_purple"),
        (COL_ORANGE, "color_orange"),
    ]

    _DRAW_TOOLS = [
        ("DRW", "freedraw"),
        ("CIR", "shape_circle"),
        ("TRI", "shape_triangle"),
        ("BOX", "shape_rectangle"),
        ("LIN", "shape_line"),
        ("HRT", "shape_heart"),
        ("ERS", "eraser"),
        ("UND", "undo"),
        ("RED", "redo"),
        ("IMG", "import_image"),
        ("GRD", "grid_toggle"),
        ("CLR", "clear"),
        ("SAV", "save"),
    ]

    _SLIDE_TOOLS = [
        ("PRE", "slide_prev"),
        ("NXT", "slide_next"),
        ("LAS", "laser_toggle"),
        ("SAV", "save"),
        ("ANN", "slide_annotate"),
        ("CLR", "clear_annotation"),
        ("LDS", "load_slides"),
    ]

    _ICON_FONT = cv2.FONT_HERSHEY_SIMPLEX
    _ICON_SCALE = 0.34
    _ICON_THICKNESS = 1

    def __init__(self, frame_width: int = DISPLAY_WIDTH) -> None:
        self._fw          = frame_width
        self._draw_btns:  list[_Btn] = []
        self._slide_btns: list[_Btn] = []
        self._slider_rect = (0, 0, 0, 0)
        self._slide_in    = 0.0          # animation progress 0→1
        self._slide_in_start = time.time()
        self._last_hovered: Optional[str] = None
        self._bar_tint = np.full((TOOLBAR_H, self._fw, 3), (12, 12, 18), dtype=np.uint8)
        self._icon_size_cache: dict[str, tuple[int, int]] = {}
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        cy = TOOLBAR_H // 2
        y1 = cy - BTN_H // 2
        y2 = y1 + BTN_H
        x  = BTN_GAP + 4

        # Colour swatches
        swatch_w = _SWATCH_R * 2 + 10
        for col, action in self._COLORS:
            self._draw_btns.append(_Btn("", action, col, (x, y1, x+swatch_w, y2)))
            x += swatch_w + 4

        x += 6
        # Slider (100px)
        self._slider_rect = (x, y1, x+100, y2)
        x += 100 + 8

        x += 6  # divider gap
        # Tool buttons
        for icon, action in self._DRAW_TOOLS:
            self._draw_btns.append(_Btn(icon, action, None, (x, y1, x+BTN_W, y2)))
            x += BTN_W + 4

        # Slide tools (separate list, same layout positions)
        x2 = BTN_GAP + 4
        for icon, action in self._SLIDE_TOOLS:
            self._slide_btns.append(_Btn(icon, action, None, (x2, y1, x2+BTN_W, y2)))
            x2 += BTN_W + 4

    # ── Hover update ──────────────────────────────────────────────────────────

    def update_hover(self, fingertip: Optional[tuple], slide_mode: bool = False) -> Optional[str]:
        """
        Call every frame. Manages hover timers.
        Returns action string when a button activates (dwell completed).
        """
        if fingertip is None:
            for btn in self._all_btns(slide_mode):
                btn.end_hover()
            self._last_hovered = None
            return None

        fx, fy = fingertip
        if fy > TOOLBAR_H:
            for btn in self._all_btns(slide_mode):
                btn.end_hover()
            return None

        activated = None
        for btn in self._all_btns(slide_mode):
            x1,y1,x2,y2 = btn.rect
            hit = x1 <= fx <= x2 and y1 <= fy <= y2
            if hit:
                btn.start_hover()
                if btn.hover_progress() >= 1.0 and self._last_hovered != btn.action:
                    btn.trigger_pulse()
                    activated = btn.action
                    self._last_hovered = btn.action
            else:
                btn.end_hover()
                if self._last_hovered == btn.action:
                    self._last_hovered = None

        return activated

    def check_hit(self, fingertip: Optional[tuple], slide_mode: bool = False) -> Optional[str]:
        """Instant hit test (no dwell) — for backward compat / keyboard bypass."""
        if fingertip is None: return None
        fx, fy = fingertip
        if fy > TOOLBAR_H: return None
        for btn in self._all_btns(slide_mode):
            x1,y1,x2,y2 = btn.rect
            if x1 <= fx <= x2 and y1 <= fy <= y2:
                return btn.action
        return None

    def slider_value(self, fingertip: Optional[tuple]) -> Optional[int]:
        if fingertip is None: return None
        fx, fy = fingertip
        x1,y1,x2,y2 = self._slider_rect
        if x1 <= fx <= x2 and y1 <= fy <= y2:
            r = (fx-x1)/max(x2-x1,1)
            return int(MIN_THICKNESS + r*(MAX_THICKNESS-MIN_THICKNESS))
        return None

    # ── Render ────────────────────────────────────────────────────────────────

    def render(
        self,
        frame:         np.ndarray,
        active_action: str,
        active_color:  tuple,
        thickness:     int,
        slide_mode:    bool = False,
    ) -> np.ndarray:
        # Slide-in animation
        age = time.time() - self._slide_in_start
        self._slide_in = min(1.0, age / 0.5)
        offset_y = int((1.0 - self._ease(self._slide_in)) * -(TOOLBAR_H + 4))

        if offset_y < 0:
            # Still animating — draw to temp surface and blit
            temp = frame.copy()
            self._render_bar(temp, active_action, active_color, thickness, slide_mode)
            roi = temp[0:TOOLBAR_H+offset_y, :]
            frame[0:TOOLBAR_H+offset_y, :] = roi
        else:
            self._render_bar(frame, active_action, active_color, thickness, slide_mode)

        return frame

    def _render_bar(self, frame, active_action, active_color, thickness, slide_mode):
        fw = self._fw

        # Background
        bar_roi = frame[0:TOOLBAR_H, 0:fw]
        cv2.addWeighted(self._bar_tint, _BG_ALPHA, bar_roi, 1-_BG_ALPHA, 0, bar_roi)

        # Bottom border line (thin, glowing)
        cv2.line(frame,(0,TOOLBAR_H),(fw,TOOLBAR_H), UI_ACCENT, 1)

        # Dividers
        cy = TOOLBAR_H//2
        sx1,_,sx2,_ = self._slider_rect
        for dv in [sx1-8, sx2+8]:
            cv2.line(frame,(dv,cy-16),(dv,cy+16),_DIVIDER,1)

        # Slider (only in draw mode)
        if not slide_mode:
            self._render_slider(frame, thickness)

        # Buttons
        btns = self._slide_btns if slide_mode else self._draw_btns
        for btn in btns:
            self._render_btn(frame, btn, active_action)

        # Mode badge
        mode_txt = "SLIDES" if slide_mode else "DRAW"
        cv2.putText(frame, mode_txt,
                    (fw-72, TOOLBAR_H-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, UI_MUTED, 1, cv2.LINE_AA)

    def _render_btn(self, frame, btn: _Btn, active: str) -> None:
        x1,y1,x2,y2 = btn.rect
        is_active = (btn.action == active)
        cx,cy     = (x1+x2)//2, (y1+y2)//2
        hov       = btn.hover_progress()
        pulse     = btn.pulse_alpha()

        # ── Colour swatch ──
        if btn.color is not None:
            r = _SWATCH_R + (3 if is_active else int(hov * 2))
            if is_active:
                cv2.circle(frame,(cx,cy), r+3, (255,255,255), cv2.FILLED)
            cv2.circle(frame,(cx,cy), r, btn.color, cv2.FILLED)

            # Hover ring
            if hov > 0:
                ring_r = r + 4
                ring_col = tuple(min(255, int(c * (0.35 + 0.65 * hov))) for c in UI_ACCENT)
                cv2.circle(frame, (cx, cy), ring_r, ring_col, 1, cv2.LINE_AA)

            # Active underline dot
            if is_active:
                cv2.circle(frame,(cx,y2+5), 3, UI_ACCENT, cv2.FILLED)
            # Hover progress arc
            if hov > 0 and not is_active:
                self._draw_arc(frame, cx, cy, _SWATCH_R+5, hov, UI_ACCENT2)
            return

        # ── Tool pill button ──
        bg  = _PILL_ACT if is_active else (_PILL_HOV if hov > 0.1 else _PILL_IDLE)
        txt = _TEXT_ACT if is_active else _TEXT_IDLE

        # Danger tint for destructive actions
        if btn.action in ("clear","clear_annotation") and not is_active:
            txt = UI_DANGER

        # Pill background
        rr = 6
        for rect in [
            (x1+rr,y1,x2-rr,y2),(x1,y1+rr,x2,y2-rr)
        ]:
            cv2.rectangle(frame,rect[:2],rect[2:],bg,cv2.FILLED)
        for corner in [(x1+rr,y1+rr),(x2-rr,y1+rr),(x1+rr,y2-rr),(x2-rr,y2-rr)]:
            cv2.circle(frame,corner,rr,bg,cv2.FILLED)

        # Hover glow outline
        if hov > 0.05 and not is_active:
            glow_col = tuple(min(255, int(c * (0.35 + 0.65 * hov))) for c in UI_ACCENT)
            cv2.rectangle(frame, (x1+1, y1+1), (x2-1, y2-1), glow_col, 1, cv2.LINE_AA)

        # Pulse ring
        if pulse > 0:
            exp = int((1-pulse)*20)
            pulse_col = tuple(min(255, int(c * (0.5 + 0.5 * pulse))) for c in UI_ACCENT)
            cv2.rectangle(frame, (x1-exp, y1-exp), (x2+exp, y2+exp), pulse_col, 1, cv2.LINE_AA)

        # Icon
        tw, th = self._icon_metrics(btn.icon)
        cv2.putText(
            frame,
            btn.icon,
            (cx - tw // 2, cy + th // 2),
            self._ICON_FONT,
            self._ICON_SCALE,
            txt,
            self._ICON_THICKNESS,
            cv2.LINE_AA,
        )

        # Active dot
        if is_active:
            cv2.circle(frame,(cx,y2+5),3,UI_ACCENT,cv2.FILLED)

        # Hover progress arc
        if hov > 0 and not is_active:
            self._draw_arc(frame,cx,cy,max(BTN_W,BTN_H)//2+4,hov,UI_ACCENT)

    def _render_slider(self, frame, thickness: int) -> None:
        x1,y1,x2,y2 = self._slider_rect
        cy = (y1+y2)//2
        cv2.line(frame,(x1,cy),(x2,cy),(40,38,55),2)
        r  = (thickness-MIN_THICKNESS)/max(MAX_THICKNESS-MIN_THICKNESS,1)
        fx = int(x1+r*(x2-x1))
        cv2.line(frame,(x1,cy),(fx,cy),UI_ACCENT,2)
        cv2.circle(frame,(fx,cy),7,(255,255,255),cv2.FILLED)
        cv2.circle(frame,(fx,cy),7,UI_ACCENT,1)
        label = str(thickness)
        (tw,_),_ = cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.36,1)
        cv2.putText(frame,label,(fx-tw//2,y1-3),
                    cv2.FONT_HERSHEY_SIMPLEX,0.36,UI_MUTED,1,cv2.LINE_AA)

    def _draw_arc(self, frame, cx, cy, r, progress, color):
        """Draw a progress arc around a button (0–1)."""
        start = -90
        end   = start + int(progress * 360)
        pts   = []
        steps = max(2, int(progress * 36))
        for i in range(steps+1):
            angle = math.radians(start + (end-start)*i/steps)
            pts.append((int(cx+r*math.cos(angle)), int(cy+r*math.sin(angle))))
        for i in range(len(pts)-1):
            cv2.line(frame, pts[i], pts[i+1], color, 1, cv2.LINE_AA)

    def _all_btns(self, slide_mode: bool) -> list[_Btn]:
        return self._slide_btns if slide_mode else self._draw_btns

    def _icon_metrics(self, icon: str) -> tuple[int, int]:
        metrics = self._icon_size_cache.get(icon)
        if metrics is None:
            (tw, th), _ = cv2.getTextSize(
                icon,
                self._ICON_FONT,
                self._ICON_SCALE,
                self._ICON_THICKNESS,
            )
            metrics = (tw, th)
            self._icon_size_cache[icon] = metrics
        return metrics

    @staticmethod
    def _ease(t: float) -> float:
        """Ease-out cubic."""
        return 1 - (1-t)**3

    @property
    def height(self) -> int:
        return TOOLBAR_H
