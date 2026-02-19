"""
canvas_engine.py
----------------
4.0 Canvas with:
  • BGRA drawing layer + undo/redo (40 levels)
  • Grid / ruled background modes
  • Shape drawing: rect, circle, ellipse, triangle, line, heart
  • Alpha-blended shape preview
  • blit_image for media import
  • save (PNG + transparent)
"""

from __future__ import annotations

import datetime
import math
import os
from typing import Optional

import cv2
import numpy as np

from utils.config import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, CANVAS_ALPHA,
    MAX_UNDO_STEPS, GRID_CELL_SIZE, SHAPE_PREVIEW_ALPHA,
    SAVE_DIR, SAVE_PREFIX, UI_BORDER,
)


class CanvasEngine:

    def __init__(self, w=DISPLAY_WIDTH, h=DISPLAY_HEIGHT, alpha=CANVAS_ALPHA):
        self._w, self._h = w, h
        self._alpha      = alpha
        self._alpha_scale = float(alpha) / 255.0
        self._canvas     = self._blank()
        self._bbox: Optional[tuple[int, int, int, int]] = None
        self._bbox_stale = False
        self._undo: list[np.ndarray] = []
        self._redo: list[np.ndarray] = []
        self._bg_mode    = "none"   # "none" | "grid" | "ruled"

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_line(self, p1, p2, color, thickness, eraser=False):
        start = p1 if p1 else p2
        c = (0, 0, 0, 0) if eraser else (*color[:3], 255)
        cv2.line(self._canvas, start, p2, c, thickness, cv2.LINE_AA)
        pad = max(2, int(thickness) + 2)
        self._mark_bbox(
            min(start[0], p2[0]) - pad,
            min(start[1], p2[1]) - pad,
            max(start[0], p2[0]) + pad,
            max(start[1], p2[1]) + pad,
            stale=eraser,
        )

    def draw_dot(self, pt, color, thickness):
        c = (*color[:3], 255)
        cv2.circle(self._canvas, pt, max(1, thickness//2), c, cv2.FILLED, cv2.LINE_AA)
        r = max(1, thickness // 2) + 2
        self._mark_bbox(pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r)

    def draw_shape(self, shape, p1, p2, color, thickness, filled=False):
        c    = (*color[:3], 255)
        fill = cv2.FILLED if filled else thickness
        x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1])
        x2, y2 = max(p1[0], p2[0]), max(p1[1], p2[1])
        cx, cy = (x1+x2)//2, (y1+y2)//2

        if shape == "rectangle":
            cv2.rectangle(self._canvas, (x1,y1),(x2,y2), c, fill, cv2.LINE_AA)
        elif shape == "circle":
            r = max(1, int(((x2-x1)**2+(y2-y1)**2)**0.5//2))
            cv2.circle(self._canvas,(cx,cy),r,c,fill,cv2.LINE_AA)
        elif shape == "ellipse":
            ax,ay = max(1,(x2-x1)//2), max(1,(y2-y1)//2)
            cv2.ellipse(self._canvas,(cx,cy),(ax,ay),0,0,360,c,fill,cv2.LINE_AA)
        elif shape == "line":
            cv2.line(self._canvas,p1,p2,c,thickness,cv2.LINE_AA)
        elif shape == "triangle":
            pts = np.array([[(x1+x2)//2,y1],[x1,y2],[x2,y2]],np.int32)
            if filled: cv2.fillPoly(self._canvas,[pts],c)
            else: cv2.polylines(self._canvas,[pts],True,c,thickness,cv2.LINE_AA)
        elif shape == "heart":
            self._draw_heart(cx, cy, max(x2-x1, y2-y1)//2, c, thickness, filled)
        pad = max(2, int(thickness) + 2)
        if shape == "line":
            self._mark_bbox(
                min(p1[0], p2[0]) - pad,
                min(p1[1], p2[1]) - pad,
                max(p1[0], p2[0]) + pad,
                max(p1[1], p2[1]) + pad,
            )
        else:
            self._mark_bbox(x1 - pad, y1 - pad, x2 + pad, y2 + pad)

    def _draw_heart(self, cx, cy, size, color, thickness, filled=False):
        """Draw a heart shape using parametric equations."""
        pts = []
        for deg in range(0, 361, 3):
            t = math.radians(deg)
            x = int(cx + size * 0.85 * math.sin(t)**3)
            y = int(cy - size * 0.75 * (
                0.8125*math.cos(t) - 0.3125*math.cos(2*t)
                - 0.125*math.cos(3*t) - 0.0625*math.cos(4*t)
            ))
            pts.append([x, y])
        pts = np.array(pts, np.int32)
        if filled:
            cv2.fillPoly(self._canvas, [pts], color)
        else:
            cv2.polylines(self._canvas, [pts], True, color, thickness, cv2.LINE_AA)

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def push_undo(self):
        if len(self._undo) >= MAX_UNDO_STEPS:
            self._undo.pop(0)
        self._undo.append(self._canvas.copy())
        self._redo.clear()

    def undo(self) -> bool:
        if not self._undo: return False
        self._redo.append(self._canvas.copy())
        self._canvas = self._undo.pop()
        self._bbox_stale = True
        return True

    def redo(self) -> bool:
        if not self._redo: return False
        self._undo.append(self._canvas.copy())
        self._canvas = self._redo.pop()
        self._bbox_stale = True
        return True

    def clear(self):
        self.push_undo()
        self._canvas = self._blank()
        self._bbox = None
        self._bbox_stale = False

    # ── Background mode ───────────────────────────────────────────────────────

    def set_bg_mode(self, mode: str):
        """mode: 'none' | 'grid' | 'ruled'"""
        self._bg_mode = mode

    def _draw_bg(self, frame: np.ndarray) -> np.ndarray:
        if self._bg_mode == "none":
            return frame
        h, w = frame.shape[:2]
        out  = frame.copy()
        col  = (30, 30, 42)
        if self._bg_mode == "grid":
            for x in range(0, w, GRID_CELL_SIZE):
                cv2.line(out, (x,0),(x,h), col, 1)
            for y in range(0, h, GRID_CELL_SIZE):
                cv2.line(out, (0,y),(w,y), col, 1)
        elif self._bg_mode == "ruled":
            for y in range(GRID_CELL_SIZE, h, GRID_CELL_SIZE):
                cv2.line(out, (0,y),(w,y), col, 1)
        return out

    # ── Blend ─────────────────────────────────────────────────────────────────

    def blend(self, camera_frame: np.ndarray) -> np.ndarray:
        base = self._draw_bg(camera_frame)
        h, w = base.shape[:2]
        c    = self._canvas
        if c.shape[:2] != (h,w):
            c = cv2.resize(c,(w,h))
            alpha_plane = c[:, :, 3]
            if not np.any(alpha_plane):
                return base
            nz = cv2.findNonZero(alpha_plane)
            if nz is None:
                return base
            x, y, bw, bh = cv2.boundingRect(nz)
            bbox = (x, y, x + bw, y + bh)
        else:
            if self._bbox_stale:
                self._recompute_bbox()
            bbox = self._bbox
            if bbox is None:
                return base

        x1, y1, x2, y2 = bbox
        alpha_plane = c[y1:y2, x1:x2, 3]
        if not np.any(alpha_plane):
            if c.shape[:2] == (self._h, self._w):
                self._bbox_stale = True
                self._recompute_bbox()
                if self._bbox is None:
                    return base
                x1, y1, x2, y2 = self._bbox
                alpha_plane = c[y1:y2, x1:x2, 3]
                if not np.any(alpha_plane):
                    return base
            else:
                return base

        out = base.copy()
        w2 = alpha_plane.astype(np.float32) * self._alpha_scale
        w1 = 1.0 - w2
        roi_base = out[y1:y2, x1:x2]
        roi_canvas = c[y1:y2, x1:x2, :3]
        out[y1:y2, x1:x2] = cv2.blendLinear(roi_base, roi_canvas, w1, w2)
        return out

    def blend_with_preview(self, camera_frame, shape, p1, p2, color, thickness) -> np.ndarray:
        out = self.blend(camera_frame)
        x1,y1 = min(p1[0],p2[0]), min(p1[1],p2[1])
        x2,y2 = max(p1[0],p2[0]), max(p1[1],p2[1])
        cx,cy  = (x1+x2)//2, (y1+y2)//2
        c      = color[:3]
        t      = max(1, thickness)

        # Semi-transparent preview overlay
        overlay = out.copy()
        if shape == "rectangle":
            cv2.rectangle(overlay,(x1,y1),(x2,y2),c,t,cv2.LINE_AA)
        elif shape == "circle":
            r = max(1,int(((x2-x1)**2+(y2-y1)**2)**0.5//2))
            cv2.circle(overlay,(cx,cy),r,c,t,cv2.LINE_AA)
        elif shape == "ellipse":
            ax,ay = max(1,(x2-x1)//2), max(1,(y2-y1)//2)
            cv2.ellipse(overlay,(cx,cy),(ax,ay),0,0,360,c,t,cv2.LINE_AA)
        elif shape == "line":
            cv2.line(overlay,p1,p2,c,t,cv2.LINE_AA)
        elif shape == "triangle":
            pts = np.array([[(x1+x2)//2,y1],[x1,y2],[x2,y2]],np.int32)
            cv2.polylines(overlay,[pts],True,c,t,cv2.LINE_AA)
        elif shape == "heart":
            self._preview_heart(overlay,cx,cy,max(x2-x1,y2-y1)//2,c,t)

        cv2.addWeighted(overlay, SHAPE_PREVIEW_ALPHA, out, 1-SHAPE_PREVIEW_ALPHA, 0, out)
        # Dashed bounding box
        cv2.rectangle(out,(x1,y1),(x2,y2),(80,80,100),1,cv2.LINE_AA)
        return out

    def _preview_heart(self, frame, cx, cy, size, color, thickness):
        pts = []
        for deg in range(0,361,4):
            t = math.radians(deg)
            x = int(cx + size*0.85*math.sin(t)**3)
            y = int(cy - size*0.75*(0.8125*math.cos(t)-0.3125*math.cos(2*t)
                                    -0.125*math.cos(3*t)-0.0625*math.cos(4*t)))
            pts.append([x,y])
        cv2.polylines(frame,[np.array(pts,np.int32)],True,color,thickness,cv2.LINE_AA)

    # ── Save ──────────────────────────────────────────────────────────────────

    def save(self, blended, username="user") -> str:
        os.makedirs(SAVE_DIR, exist_ok=True)
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SAVE_DIR, f"{SAVE_PREFIX}_{username}_{ts}.png")
        cv2.imwrite(path, blended)
        return path

    def save_transparent(self, username="user") -> str:
        os.makedirs(SAVE_DIR, exist_ok=True)
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SAVE_DIR, f"{SAVE_PREFIX}_{username}_{ts}_transparent.png")
        cv2.imwrite(path, self._canvas)
        return path

    def blit_image(self, img_bgra: np.ndarray, x: int, y: int):
        ih,iw = img_bgra.shape[:2]
        x2,y2 = min(x+iw,self._w), min(y+ih,self._h)
        iw,ih = x2-x, y2-y
        if iw<=0 or ih<=0: return
        patch = img_bgra[:ih,:iw]
        if patch.shape[2]==4:
            a = patch[:,:,3:4].astype(np.float32)/255.0
            for c in range(3):
                self._canvas[y:y2,x:x2,c] = (
                    self._canvas[y:y2,x:x2,c]*(1-a[:,:,0]) + patch[:,:,c]*a[:,:,0]
                ).astype(np.uint8)
            self._canvas[y:y2,x:x2,3] = np.maximum(self._canvas[y:y2,x:x2,3],patch[:,:,3])
        else:
            self._canvas[y:y2,x:x2,:3] = patch[:ih,:iw,:3]
            self._canvas[y:y2,x:x2,3]  = 255
        self._mark_bbox(x, y, x2, y2)

    def _mark_bbox(self, x1: int, y1: int, x2: int, y2: int, stale: bool = False) -> None:
        if stale:
            self._bbox_stale = True
            return
        x1 = max(0, min(self._w, int(x1)))
        y1 = max(0, min(self._h, int(y1)))
        x2 = max(0, min(self._w, int(x2)))
        y2 = max(0, min(self._h, int(y2)))
        if x2 <= x1 or y2 <= y1:
            return
        if self._bbox is None:
            self._bbox = (x1, y1, x2, y2)
        else:
            bx1, by1, bx2, by2 = self._bbox
            self._bbox = (min(bx1, x1), min(by1, y1), max(bx2, x2), max(by2, y2))
        self._bbox_stale = False

    def _recompute_bbox(self) -> None:
        alpha_plane = self._canvas[:, :, 3]
        nz = cv2.findNonZero(alpha_plane)
        if nz is None:
            self._bbox = None
        else:
            x, y, w, h = cv2.boundingRect(nz)
            self._bbox = (x, y, x + w, y + h)
        self._bbox_stale = False

    def _blank(self):
        return np.zeros((self._h, self._w, 4), dtype=np.uint8)
