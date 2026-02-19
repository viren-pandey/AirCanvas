"""state_manager.py — 4.0 centralised app state."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from utils.config import (
    AUTO_CAPTURE_DEFAULT_ENABLED,
    AUTO_CAPTURE_INTERVAL_SEC,
    COL_GREEN,
    DEFAULT_THICKNESS,
    DEPTH_MODE,
)


class DrawingState:
    IDLE = "IDLE"
    ARMED = "ARMED"
    DRAWING = "DRAWING"
    SHAPE_PREVIEW = "SHAPE_PREVIEW"
    COMMITTED = "COMMITTED"
    PAUSED = "PAUSED"

    ALL = {
        IDLE,
        ARMED,
        DRAWING,
        SHAPE_PREVIEW,
        COMMITTED,
        PAUSED,
    }


@dataclass
class AppState:
    username:         str   = "Artist"
    mirror_mode:      bool  = True
    tracking_active:  bool  = True
    show_landmarks:   bool  = False

    # Drawing
    drawing_active:   bool  = False
    prev_point:       object = None
    active_color:     tuple = field(default_factory=lambda: COL_GREEN)
    thickness:        int   = DEFAULT_THICKNESS
    eraser_mode:      bool  = False
    active_action:    str   = "color_green"

    # Shape
    shape_mode:       bool  = False
    active_shape:     str   = "rectangle"

    # Voice
    voice_enabled:    bool  = True
    last_voice_cmd:   str   = ""

    # Depth
    depth_blocked:    bool  = False
    depth_mode:       str   = DEPTH_MODE

    # Presentation
    slide_mode:       bool  = False
    laser_mode:       bool  = False
    slide_annotate:   bool  = False

    # Grid
    grid_enabled:     bool  = False
    bg_mode:          str   = "none"

    # Force stop
    force_stop:       bool  = False

    # Explicit drawing state machine
    drawing_state:    str   = DrawingState.IDLE
    last_state_reason: str  = ""
    last_state_ts:    float = 0.0

    # Optional auto-capture mode
    auto_capture_enabled: bool = AUTO_CAPTURE_DEFAULT_ENABLED
    auto_capture_interval_sec: float = AUTO_CAPTURE_INTERVAL_SEC

    def set_drawing_state(self, new_state: str, reason: str = "") -> bool:
        """Transition the drawing state and emit a lightweight log line."""
        if new_state not in DrawingState.ALL:
            raise ValueError(f"Invalid drawing state: {new_state}")
        if self.drawing_state == new_state:
            return False
        old_state = self.drawing_state
        self.drawing_state = new_state
        self.last_state_reason = reason
        self.last_state_ts = time.time()
        suffix = f" ({reason})" if reason else ""
        print(f"[DRAW_STATE] {old_state} -> {new_state}{suffix}")
        return True
