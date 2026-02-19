"""
command_parser.py — 4.0
-----------------------
Keyword parser for voice commands.

Trigger: "canvas" (or mis-recognitions: "campus", "cameras")
Exception: "stop" / "stop drawing" — no trigger needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class CommandType(Enum):
    STOP          = auto()
    DRAW_SHAPE    = auto()
    FREE_DRAW     = auto()
    CONFIRM_SHAPE = auto()
    SET_COLOR     = auto()
    BRUSH_UP      = auto()
    BRUSH_DOWN    = auto()
    BRUSH_SET     = auto()
    CLEAR         = auto()
    SAVE          = auto()
    PAUSE         = auto()
    RESUME        = auto()
    UNDO          = auto()
    REDO          = auto()
    IMPORT_IMAGE  = auto()
    SLIDE_MODE    = auto()
    DRAW_MODE     = auto()
    NEXT_SLIDE    = auto()
    PREV_SLIDE    = auto()
    GRID_TOGGLE   = auto()
    UNKNOWN       = auto()


@dataclass
class VoiceCommand:
    type:    CommandType
    payload: dict = field(default_factory=dict)
    raw:     str  = ""


_TRIGGER_RE = re.compile(
    r"(?:\bcanvas\b|\bcanva\b|\bcanvass\b|\bcampus\b|\bcameras?\b|\bcamvas\b|\bcancer\b|\bcan\s+this\b|\bcan\s+bus\b)"
)
_CANVAS_STOP_RE = re.compile(r"\b(?:canvas|canva|canvass|campus|cameras?|camvas)\s+stop(?:\s+drawing)?\b")
_CANVAS_START_RE = re.compile(r"\b(?:canvas|canva|canvass|campus|cameras?|camvas)\s+start\b")
_DIRECT_COMMAND_HINTS = (
    "draw", "shape", "free draw", "freehand",
    "color", "colour", "change", "switch",
    "brush", "size", "thickness", "stroke",
    "clear", "wipe", "erase all", "reset",
    "save", "export", "store",
    "pause", "resume", "continue", "start", "stop", "undo", "redo",
    "import", "load image", "open image", "add image", "add photo",
    "grid", "snap", "guide",
    "slide mode", "presentation", "slideshow",
    "draw mode", "drawing mode", "back to draw",
    "next slide", "prev slide", "previous slide",
)

_SHAPES = {
    "rectangle":"rectangle","rect":"rectangle","square":"rectangle",
    "circle":"circle","round":"circle","oval":"ellipse",
    "triangle":"triangle","tri":"triangle",
    "line":"line","ellipse":"ellipse",
    "heart":"heart","love":"heart",
}

_COLORS = {
    "red":"color_red","green":"color_green","blue":"color_blue",
    "black":"color_black","yellow":"color_yellow",
    "purple":"color_purple","orange":"color_orange","white":"color_white",
}


class CommandParser:

    def parse(self, text: str) -> Optional[VoiceCommand]:
        text = text.lower().strip()
        if not text:
            return None

        if _CANVAS_STOP_RE.search(text):
            return VoiceCommand(CommandType.STOP, raw=text)
        if _CANVAS_START_RE.search(text):
            return VoiceCommand(CommandType.RESUME, raw=text)

        # Stop: no trigger needed
        if self._is_stop(text):
            return VoiceCommand(CommandType.STOP, raw=text)

        cleaned, had_trigger = self._strip_trigger(text)
        if not had_trigger and not self._looks_like_direct_command(text):
            return None

        cmd = self._parse_command(cleaned if had_trigger else text)
        if cmd:
            cmd.raw = text
            return cmd
        return VoiceCommand(CommandType.UNKNOWN, raw=text) if had_trigger else None

    def _is_stop(self, t):
        return re.search(r"\bstop\b", t) is not None

    def _strip_trigger(self, text: str) -> tuple[str, bool]:
        cleaned = _TRIGGER_RE.sub(" ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.")
        return cleaned, cleaned != text

    @staticmethod
    def _looks_like_direct_command(text: str) -> bool:
        return any(k in text for k in _DIRECT_COMMAND_HINTS)

    def _parse_command(self, text: str) -> Optional[VoiceCommand]:
        return (
            self._draw_shape(text) or
            self._free_draw(text) or
            self._confirm(text) or
            self._color(text) or
            self._brush(text) or
            self._slides(text) or
            self._system(text)
        )

    def _draw_shape(self, t):
        if "draw" not in t and "shape" not in t: return None
        for k,v in _SHAPES.items():
            if k in t: return VoiceCommand(CommandType.DRAW_SHAPE, {"shape":v})
        return None

    def _free_draw(self, t):
        if any(k in t for k in ("free draw","freehand","free mode","freestyle")):
            return VoiceCommand(CommandType.FREE_DRAW)
        return None

    def _confirm(self, t):
        if any(k in t for k in ("confirm","done","finish","finalize","complete")):
            return VoiceCommand(CommandType.CONFIRM_SHAPE)
        return None

    def _color(self, t):
        if not any(k in t for k in ("color","colour","change","switch")): return None
        for k,v in _COLORS.items():
            if k in t: return VoiceCommand(CommandType.SET_COLOR, {"action":v})
        return None

    def _brush(self, t):
        if not any(k in t for k in ("brush","size","thickness","stroke")): return None
        m = re.search(r"\b(\d+)\b", t)
        if m and any(k in t for k in ("set", "to", "size", "thickness")):
            return VoiceCommand(CommandType.BRUSH_SET, {"size": int(m.group(1))})
        if any(k in t for k in ("increase","bigger","larger","up","more","thicker")):
            return VoiceCommand(CommandType.BRUSH_UP)
        if any(k in t for k in ("decrease","smaller","reduce","down","less","thinner")):
            return VoiceCommand(CommandType.BRUSH_DOWN)
        return None

    def _slides(self, t):
        if any(k in t for k in ("slide mode","presentation","slideshow")):
            return VoiceCommand(CommandType.SLIDE_MODE)
        if any(k in t for k in ("draw mode","drawing mode","back to draw")):
            return VoiceCommand(CommandType.DRAW_MODE)
        if any(k in t for k in ("next slide","next","forward")):
            return VoiceCommand(CommandType.NEXT_SLIDE)
        if any(k in t for k in ("previous","prev slide","back","previous slide")):
            return VoiceCommand(CommandType.PREV_SLIDE)
        return None

    def _system(self, t):
        if any(k in t for k in ("clear","wipe","erase all","reset")):
            return VoiceCommand(CommandType.CLEAR)
        if any(k in t for k in ("save","export","store")):
            return VoiceCommand(CommandType.SAVE)
        if any(k in t for k in ("pause","freeze","hold")):
            return VoiceCommand(CommandType.PAUSE)
        if any(k in t for k in ("resume","continue","unpause","start")):
            return VoiceCommand(CommandType.RESUME)
        if "undo" in t: return VoiceCommand(CommandType.UNDO)
        if "redo" in t: return VoiceCommand(CommandType.REDO)
        if any(k in t for k in ("import","load image","open image","add image","add photo")):
            return VoiceCommand(CommandType.IMPORT_IMAGE)
        if any(k in t for k in ("grid","snap","guide")):
            return VoiceCommand(CommandType.GRID_TOGGLE)
        return None
