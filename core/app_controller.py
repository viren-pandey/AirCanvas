"""
app_controller.py â€” AntiGravity AirCanvas 4.0
==============================================
Orchestrates all subsystems:
  â€¢ Multi-hand detection (background thread)
  â€¢ Gesture engine (dual-hand combos, Kalman smoothing)
  â€¢ Advanced brush (speed-adaptive, Kalman filtered)
  â€¢ Canvas (BGRA, undo/redo, grid, heart shape)
  â€¢ Shape engine (hover-anchor â†’ drag â†’ pinch/voice confirm)
  â€¢ Animated toolbar (hover-to-activate, pulse, slide-in)
  â€¢ Slide / Presentation controller
  â€¢ Voice listener + parser (stop=no-trigger, all others need "canvas")
  â€¢ Depth guard (Z-axis)
  â€¢ All HUD overlays
"""

from __future__ import annotations

import sys
import time
import cv2
import numpy as np

from hand_tracking.multi_hand_detector import MultiHandDetector
from hand_tracking.gesture_engine      import GestureEngine, Gesture
from drawing.canvas_engine             import CanvasEngine
from drawing.advanced_brush            import AdvancedBrush
from drawing.shape_engine              import ShapeEngine
from presentation.slide_controller     import SlideController
from ui.animated_toolbar               import AnimatedToolbar
from ui.onboarding                     import OnboardingScreen
from ui.overlays                       import (
    FadeTransition, StatusToast, GestureHint, CursorGlow,
    VoiceHUD, AnchorPulse, TwoHandIndicator, FPSDisplay,
)
from performance.thread_manager        import DetectionThread
from performance.fps_optimizer         import FPSOptimizer
from core.state_manager                import AppState, DrawingState
from voice.voice_listener              import VoiceListener
from voice.command_parser              import CommandParser, CommandType
from services.frame_uploader           import FrameUploader

from utils.config import (
    CAMERA_INDEX, DISPLAY_WIDTH, DISPLAY_HEIGHT, TARGET_FPS,
    WINDOW_TITLE, TOOLBAR_H, CAMERA_BUFFER_SIZE, CAMERA_FOURCC,
    COL_GREEN, COL_RED, COL_BLUE, COL_BLACK, COL_YELLOW,
    COL_PURPLE, COL_ORANGE, COL_WHITE,
    UI_ACCENT, UI_MUTED,
    VOICE_ENABLED, VOICE_LANGUAGE, VOICE_ENERGY_THRESHOLD,
    VOICE_PAUSE_THRESHOLD, VOICE_PHRASE_LIMIT,
    VOICE_BRUSH_STEP, VOICE_TOAST_DURATION,
    DEPTH_MODE, DEPTH_THRESHOLD,
    INDEX_TIP, THUMB_TIP,
    SLIDE_DIR,
)


class AppController:
    """Coordinates the real-time AirCanvas runtime components."""

    _COLOR_MAP = {
        "color_green":  COL_GREEN,
        "color_red":    COL_RED,
        "color_blue":   COL_BLUE,
        "color_black":  COL_BLACK,
        "color_yellow": COL_YELLOW,
        "color_purple": COL_PURPLE,
        "color_orange": COL_ORANGE,
        "color_white":  COL_WHITE,
    }

    def __init__(self) -> None:
        # â”€â”€ Camera â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if sys.platform.startswith("win") and hasattr(cv2, "CAP_DSHOW"):
            self._cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            print("[ERROR] Cannot open webcam. Check CAMERA_INDEX in config.py.")
            sys.exit(1)
        if CAMERA_FOURCC:
            self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*CAMERA_FOURCC))
        if CAMERA_BUFFER_SIZE > 0:
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFER_SIZE)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  DISPLAY_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS,          TARGET_FPS)

        # â”€â”€ Subsystems â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._detector  = MultiHandDetector()
        self._gesture   = GestureEngine()
        self._canvas    = CanvasEngine()
        self._brush     = AdvancedBrush()
        self._shapes    = ShapeEngine()
        self._slides    = SlideController()
        self._toolbar   = AnimatedToolbar(DISPLAY_WIDTH)
        self._onboard   = OnboardingScreen()
        self._state     = AppState()
        self._uploader  = FrameUploader.from_env()
        self._remote_session_started = False
        if self._uploader:
            self._uploader.auto_capture_enabled = self._state.auto_capture_enabled
            self._uploader.set_auto_capture_interval(self._state.auto_capture_interval_sec)
            self._uploader.start()

        # â”€â”€ Overlays â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._fade      = FadeTransition()
        self._toast     = StatusToast()
        self._hint      = GestureHint()
        self._cursor    = CursorGlow()
        self._voice_hud = VoiceHUD()
        self._anchor_pulse = AnchorPulse()
        self._two_hand  = TwoHandIndicator()
        self._fps       = FPSOptimizer()

        # â”€â”€ Background detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._det_thread = DetectionThread(self._detector.process)
        self._det_thread.start()

        # â”€â”€ Voice â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._voice     = VoiceListener(
            language=VOICE_LANGUAGE,
            energy_threshold=VOICE_ENERGY_THRESHOLD,
            pause_threshold=VOICE_PAUSE_THRESHOLD,
            phrase_limit=VOICE_PHRASE_LIMIT,
        )
        self._parser    = CommandParser()
        self._voice_active = False
        if VOICE_ENABLED:
            self._voice_active = self._voice.start()
            self._state.voice_enabled = self._voice_active

        # â”€â”€ Depth tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._ref_z:    float = 0.0
        self._stroke_started = False

        self._onboarding_done = False
        self._prev_gesture    = Gesture.NONE
        self._shape_pinch_active = False
        self._fps_sum         = 0.0
        self._fps_samples     = 0

    # â”€â”€ Main loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def run(self) -> None:
        print(f"[INFO] {WINDOW_TITLE} â€” ready")
        print("[INFO] Keys: S=Save  M=Mirror  I=Import image  O=Open slides folder")
        print("[INFO]       U/R=Undo/Redo  +/-=Brush  A=Auto-capture  [/] interval  V=Voice  G=Grid  P=Presentation  Q=Quit")
        print("[INFO] Voice: 'Canvas, draw circle'  |  just say 'Stop' to halt")

        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_TITLE, DISPLAY_WIDTH, DISPLAY_HEIGHT)

        while True:
            ret, frame = self._cap.read()
            if not ret:
                continue
            if self._state.mirror_mode:
                frame = cv2.flip(frame, 1)

            key = cv2.waitKey(1) & 0xFF

            # â”€â”€ Onboarding â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if not self._onboarding_done:
                done, name = self._onboard.update(frame, key)
                if done:
                    self._state.username = name or "Artist"
                    self._onboarding_done = True
                    self._state.set_drawing_state(DrawingState.ARMED, "onboarding complete")
                    self._fade.trigger()
                    self._toast.show(
                        f"Welcome, {self._state.username}!  Say 'Stop' to halt  |  âœ‹ draw",
                        duration=4.0
                    )
                    if self._uploader and not self._remote_session_started:
                        self._remote_session_started = True
                        print("[UPLOAD] Remote frame sync enabled.")
                cv2.imshow(WINDOW_TITLE, frame)
                if key in (ord('q'), ord('Q')):
                    break
                continue

            # â”€â”€ Voice â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            self._process_voice(frame)

            # â”€â”€ Detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if self._state.tracking_active:
                # Avoid per-frame copies here; detector thread always reads the latest frame reference.
                self._det_thread.put_frame(frame)
                hands = self._det_thread.get_result()
            else:
                hands = []

            # â”€â”€ Gesture â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            gr = self._gesture.update(hands)

            # Gesture change notification
            if gr.gesture != self._prev_gesture:
                self._on_gesture_change(gr.gesture)
                self._prev_gesture = gr.gesture

            paused_by_state = self._state.drawing_state == DrawingState.PAUSED

            # Colour from gesture
            if not paused_by_state and not self._state.eraser_mode:
                self._state.active_color = gr.color

            # Undo / redo / clear
            if gr.undo and not self._state.slide_mode and not paused_by_state:
                self._canvas.undo(); self._toast.show("â†© Undo")
            if gr.redo and not self._state.slide_mode and not paused_by_state:
                self._canvas.redo(); self._toast.show("â†ª Redo")
            if gr.clear and not paused_by_state:
                self._canvas.clear(); self._toast.show("Canvas cleared")

            # Two-hand combos
            if gr.two_hand_clear and not paused_by_state:
                self._canvas.clear()
                self._two_hand.show("ðŸ–ðŸ–  Canvas Cleared!")
            if gr.two_hand_pause and not paused_by_state:
                self._request_pause(
                    "two-hand fist pause",
                    commit_shape=True,
                    disable_tracking=False,
                    toast="âœŠâœŠ  Drawing Paused",
                )
                self._two_hand.show("âœŠâœŠ  Drawing Paused")

            # Slide navigation via swipe
            if self._state.slide_mode and not paused_by_state:
                if gr.slide_next: self._slides.next(); self._toast.show("â–· Next slide")
                if gr.slide_prev: self._slides.prev(); self._toast.show("â— Prev slide")

            # Pinch gesture â†’ brush resize
            if (
                gr.gesture == Gesture.PINCH
                and gr.pinch_delta
                and not self._state.shape_mode
                and self._state.drawing_state != DrawingState.PAUSED
            ):
                self._brush.adjust(gr.pinch_delta)
                self._state.thickness = self._brush.thickness

            # â”€â”€ Depth guard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            norm_lm = hands[0].norm_lm if hands else None
            depth_ok = self._check_depth(norm_lm)
            self._state.depth_blocked = not depth_ok
            if (
                not depth_ok
                and self._stroke_started
                and self._state.drawing_state != DrawingState.PAUSED
            ):
                self._request_pause(
                    "depth threshold exceeded",
                    commit_shape=False,
                    disable_tracking=False,
                    toast="Depth stop",
                )

            # â”€â”€ Toolbar (hover-to-activate) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            fingertip_smooth = gr.fingertip
            fingertip   = gr.fingertip_raw if gr.fingertip_raw is not None else gr.fingertip
            in_toolbar  = fingertip is not None and fingertip[1] < TOOLBAR_H

            toolbar_action = self._toolbar.update_hover(fingertip, self._state.slide_mode)
            if toolbar_action:
                self._handle_toolbar(toolbar_action, frame)

            slider_val = self._toolbar.slider_value(fingertip) if in_toolbar else None
            if slider_val is not None:
                self._brush.set_thickness(slider_val)
                self._state.thickness = self._brush.thickness

            # â”€â”€ Drawing / Shape / Slide â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            is_paused = self._state.drawing_state == DrawingState.PAUSED
            is_drawing = (
                gr.gesture == Gesture.DRAWING
                and not in_toolbar
                and self._state.tracking_active
                and depth_ok
                and not is_paused
            )
            pinch_active = gr.gesture == Gesture.PINCH
            pinch_released = self._shape_pinch_active and not pinch_active
            if self._state.shape_mode:
                self._shape_pinch_active = pinch_active
            else:
                self._shape_pinch_active = False

            if self._state.slide_mode:
                laser = (gr.gesture == Gesture.OPEN_PALM)
                self._state.laser_mode = laser
            elif self._state.shape_mode:
                self._handle_shape(is_drawing, fingertip, norm_lm, pinch_released)
            else:
                self._handle_freedraw(is_drawing, fingertip, norm_lm)
            self._tick_state_machine()

            # â”€â”€ Compose output â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if self._state.slide_mode:
                output = self._slides.render(frame, fingertip, self._state.laser_mode)
            elif self._state.shape_mode and self._shapes.has_preview:
                output = self._canvas.blend_with_preview(
                    frame, self._shapes.active_shape,
                    self._shapes.anchor, self._shapes.current,
                    self._state.active_color, self._state.thickness,
                )
            else:
                output = self._canvas.blend(frame)

            # Landmarks
            if self._state.show_landmarks and self._state.tracking_active:
                self._detector.draw_landmarks(output, hands)

            # Toolbar
            self._toolbar.render(
                output, self._state.active_action,
                self._state.active_color, self._state.thickness,
                self._state.slide_mode,
            )

            # â”€â”€ HUD overlays â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            fps_now = self._fps.tick()
            self._fps.draw(output)
            self._fps_sum += fps_now
            self._fps_samples += 1

            if self._state.shape_mode and self._shapes.state == ShapeEngine.ANCHORING:
                self._anchor_pulse.draw(output, fingertip, self._shapes.hold_progress)

            cursor_tip = fingertip_smooth if fingertip_smooth is not None else fingertip
            self._cursor.draw(output, cursor_tip, self._state.active_color,
                              is_drawing, self._state.eraser_mode)
            self._toast.draw(output)
            self._hint.draw(output)
            self._two_hand.draw(output)
            self._voice_hud.draw(output, self._voice_active, self._state.depth_blocked)
            self._draw_status(output)
            self._maybe_auto_capture(output)

            output = self._fade.apply(output)

            if self._handle_keys(key, output):
                break

            cv2.imshow(WINDOW_TITLE, output)

        self._shutdown()

    # â”€â”€ Depth guard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _check_depth(self, norm_lm) -> bool:
        if DEPTH_MODE == "off" or norm_lm is None:
            return True
        z = norm_lm[INDEX_TIP][2]
        if not self._stroke_started:
            self._ref_z = z
        delta = z - self._ref_z
        return delta <= DEPTH_THRESHOLD

    # â”€â”€ Halt â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _halt(self, reset_shape: bool = True):
        self._state.drawing_active = False
        self._state.prev_point     = None
        self._brush.reset()
        if reset_shape:
            self._shapes.cancel()
        self._stroke_started       = False
        self._shape_pinch_active   = False

    def _commit_shape_preview(self, reason: str, toast: bool = True) -> bool:
        result = self._shapes.finalize()
        if not result:
            return False
        shape, p1, p2 = result
        self._canvas.push_undo()
        self._canvas.draw_shape(
            shape, p1, p2,
            self._state.active_color, self._state.thickness,
        )
        self._state.set_drawing_state(DrawingState.COMMITTED, reason)
        self._state.set_drawing_state(DrawingState.IDLE, "shape finalization reset")
        if toast:
            self._toast.show(f"âœ“ {shape} committed")
        return True

    def _request_pause(
        self,
        reason: str,
        commit_shape: bool,
        disable_tracking: bool,
        toast: str | None = None,
    ) -> None:
        already_paused = self._state.drawing_state == DrawingState.PAUSED
        committed = False
        if commit_shape:
            committed = self._commit_shape_preview(reason, toast=False)
        self._halt(reset_shape=not committed)
        self._state.force_stop = True
        if disable_tracking:
            self._state.tracking_active = False
        self._state.set_drawing_state(DrawingState.PAUSED, reason)
        if toast and not already_paused:
            self._toast.show(toast)

    def _resume_from_pause(self, reason: str, toast: str | None = None) -> None:
        self._state.force_stop = False
        self._state.tracking_active = True
        self._state.drawing_active = False
        self._state.prev_point = None
        self._stroke_started = False
        self._shape_pinch_active = False
        self._state.set_drawing_state(DrawingState.ARMED, reason)
        if toast:
            self._toast.show(toast)

    def _tick_state_machine(self) -> None:
        state = self._state.drawing_state
        if state == DrawingState.PAUSED:
            return
        if self._state.shape_mode and self._shapes.has_preview:
            self._state.set_drawing_state(DrawingState.SHAPE_PREVIEW, "shape preview active")
            return
        if self._state.drawing_active:
            self._state.set_drawing_state(DrawingState.DRAWING, "stroke active")
            return
        if state == DrawingState.SHAPE_PREVIEW and not self._shapes.has_preview:
            self._state.set_drawing_state(DrawingState.IDLE, "shape preview ended")
            return
        if state == DrawingState.DRAWING and not self._state.drawing_active:
            self._state.set_drawing_state(DrawingState.COMMITTED, "stroke frozen")
            self._state.set_drawing_state(DrawingState.IDLE, "stroke end")
            return
        if state == DrawingState.IDLE and self._state.tracking_active and not self._state.force_stop:
            self._state.set_drawing_state(DrawingState.ARMED, "tracking active")

    # â”€â”€ Free draw â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _handle_freedraw(self, is_drawing, fingertip, norm_lm):
        if is_drawing and fingertip:
            if not self._state.drawing_active:
                self._canvas.push_undo()
                if norm_lm: self._ref_z = norm_lm[INDEX_TIP][2]
                self._stroke_started   = True
                self._state.drawing_active = True
                self._state.set_drawing_state(DrawingState.DRAWING, "free-draw started")
            color, thick = self._brush.draw_params(self._state.active_color)
            pt = self._brush.smooth(fingertip)
            self._canvas.draw_line(
                self._state.prev_point, pt,
                color, thick, eraser=self._state.eraser_mode,
            )
            self._state.prev_point = pt
        else:
            if self._state.drawing_active:
                self._stroke_started = False
                self._state.set_drawing_state(DrawingState.COMMITTED, "free-draw ended")
                self._state.set_drawing_state(DrawingState.IDLE, "awaiting re-arm")
            self._state.drawing_active = False
            self._state.prev_point     = None
            self._brush.reset()

    # â”€â”€ Shape â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _handle_shape(self, is_drawing, fingertip, norm_lm, pinch_released):
        if is_drawing and norm_lm is not None and not self._stroke_started:
            self._ref_z = norm_lm[INDEX_TIP][2]
            self._stroke_started = True
        if not is_drawing and self._state.drawing_state != DrawingState.SHAPE_PREVIEW:
            self._stroke_started = False
        self._shapes.update(fingertip, is_drawing)
        if self._shapes.has_preview:
            self._state.set_drawing_state(DrawingState.SHAPE_PREVIEW, "shape preview active")
        if pinch_released and self._shapes.has_preview:
            self._commit_shape_preview("pinch released")
            self._stroke_started = False

    # â”€â”€ Voice processing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _process_voice(self, frame):
        if not self._voice_active:
            return
        text = self._voice.get_text()
        if not text:
            return
        self._state.last_voice_cmd = text
        cmd = self._parser.parse(text)
        if cmd is None or cmd.type == CommandType.UNKNOWN:
            return

        label = self._cmd_label(cmd.type, cmd.payload)
        self._voice_hud.show_command(label, VOICE_TOAST_DURATION)
        self._dispatch_voice(cmd, frame)

    def _dispatch_voice(self, cmd, frame):
        t = cmd.type

        if t == CommandType.STOP:
            self._request_pause(
                "voice stop",
                commit_shape=True,
                disable_tracking=True,
                toast="🛑 Stop",
            )

        elif t == CommandType.DRAW_SHAPE:
            shape = cmd.payload.get("shape", "rectangle")
            self._state.shape_mode   = True
            self._state.active_shape = shape
            self._shapes.set_shape(shape)
            self._state.active_action = f"shape_{shape}"
            self._toast.show(f"ðŸŽ™ Shape: {shape}")

        elif t == CommandType.FREE_DRAW:
            self._state.shape_mode   = False
            self._toast.show("ðŸŽ™ Free draw")

        elif t == CommandType.CONFIRM_SHAPE:
            self._toast.show("Release pinch or say 'Canvas stop' to finalize")

        elif t == CommandType.SET_COLOR:
            action = cmd.payload.get("action", "color_green")
            if action in self._COLOR_MAP:
                self._state.active_color  = self._COLOR_MAP[action]
                self._state.active_action = action
                self._state.eraser_mode   = False
                self._brush.eraser        = False
                self._toast.show(f"ðŸŽ™ {action.replace('color_','').title()}")

        elif t == CommandType.BRUSH_UP:
            self._brush.adjust(VOICE_BRUSH_STEP)
            self._state.thickness = self._brush.thickness
            self._toast.show(f"ðŸŽ™ Brush {self._state.thickness}px")

        elif t == CommandType.BRUSH_DOWN:
            self._brush.adjust(-VOICE_BRUSH_STEP)
            self._state.thickness = self._brush.thickness
            self._toast.show(f"ðŸŽ™ Brush {self._state.thickness}px")

        elif t == CommandType.BRUSH_SET:
            self._brush.set_thickness(cmd.payload.get("size", self._state.thickness))
            self._state.thickness = self._brush.thickness
            self._toast.show(f"ðŸŽ™ Brush {self._state.thickness}px")

        elif t == CommandType.CLEAR:
            self._canvas.clear()
            self._state.prev_point = None
            self._toast.show("ðŸŽ™ Cleared!")

        elif t == CommandType.SAVE:
            blended = self._canvas.blend(frame)
            self._save_current_frame(blended, source="voice")

        elif t == CommandType.PAUSE:
            self._request_pause(
                "voice pause",
                commit_shape=False,
                disable_tracking=True,
                toast="ðŸŽ™ Paused",
            )

        elif t == CommandType.RESUME:
            self._resume_from_pause("voice start", toast="ðŸŽ™ Resumed")

        elif t == CommandType.UNDO:
            if self._canvas.undo(): self._toast.show("ðŸŽ™ â†© Undo")

        elif t == CommandType.REDO:
            if self._canvas.redo(): self._toast.show("ðŸŽ™ â†ª Redo")

        elif t == CommandType.SLIDE_MODE:
            self._state.slide_mode  = True
            self._state.active_action = "slide_mode"
            self._toast.show("ðŸŽ™ Presentation mode")

        elif t == CommandType.DRAW_MODE:
            self._state.slide_mode  = False
            self._toast.show("ðŸŽ™ Draw mode")

        elif t == CommandType.NEXT_SLIDE:
            self._slides.next(); self._toast.show("â–· Next")

        elif t == CommandType.PREV_SLIDE:
            self._slides.prev(); self._toast.show("â— Prev")

        elif t == CommandType.GRID_TOGGLE:
            self._toggle_grid()

        elif t == CommandType.IMPORT_IMAGE:
            self._import_image()

    @staticmethod
    def _cmd_label(t, payload):
        labels = {
            CommandType.STOP:          "Stop",
            CommandType.DRAW_SHAPE:    f"Draw {payload.get('shape','')}",
            CommandType.FREE_DRAW:     "Free draw",
            CommandType.CONFIRM_SHAPE: "Confirm shape",
            CommandType.SET_COLOR:     payload.get('action','').replace('color_','').title(),
            CommandType.BRUSH_UP:      "Brush â†‘",
            CommandType.BRUSH_DOWN:    "Brush â†“",
            CommandType.BRUSH_SET:     f"Brush {payload.get('size','')}",
            CommandType.CLEAR:         "Clear",
            CommandType.SAVE:          "Save",
            CommandType.PAUSE:         "Pause",
            CommandType.RESUME:        "Resume",
            CommandType.UNDO:          "Undo",
            CommandType.REDO:          "Redo",
            CommandType.SLIDE_MODE:    "Slide mode",
            CommandType.DRAW_MODE:     "Draw mode",
            CommandType.NEXT_SLIDE:    "Next slide",
            CommandType.PREV_SLIDE:    "Prev slide",
            CommandType.GRID_TOGGLE:   "Grid toggle",
            CommandType.IMPORT_IMAGE:  "Import image",
        }
        return labels.get(t, "?")

    # â”€â”€ Toolbar handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _handle_toolbar(self, action: str, frame=None) -> None:
        if action in self._COLOR_MAP:
            self._state.active_color  = self._COLOR_MAP[action]
            self._state.active_action = action
            self._state.eraser_mode   = False
            self._brush.eraser        = False

        elif action == "freedraw":
            self._state.shape_mode   = False
            self._state.active_action = "freedraw"

        elif action == "eraser":
            self._state.eraser_mode   = True
            self._state.active_action = "eraser"
            self._brush.eraser        = True

        elif action.startswith("shape_"):
            shape = action.replace("shape_", "")
            self._state.shape_mode    = True
            self._state.active_shape  = shape
            self._shapes.set_shape(shape)
            self._state.active_action = action
            self._toast.show(f"Shape: {shape} â€” hold still to anchor")

        elif action == "undo":
            if self._canvas.undo(): self._toast.show("â†© Undo")

        elif action == "redo":
            if self._canvas.redo(): self._toast.show("â†ª Redo")

        elif action == "grid_toggle":
            self._toggle_grid()

        elif action == "import_image":
            self._import_image()

        elif action == "clear":
            self._canvas.clear()
            self._state.prev_point = None
            self._toast.show("Canvas cleared")

        elif action == "save":
            if frame is not None:
                blended = self._canvas.blend(frame)
            else:
                blended = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), np.uint8)
            self._save_current_frame(blended, source="toolbar")

        # Slide actions
        elif action == "slide_prev":
            self._slides.prev(); self._toast.show("â— Prev")

        elif action == "slide_next":
            self._slides.next(); self._toast.show("â–· Next")

        elif action == "laser_toggle":
            self._state.laser_mode = not self._state.laser_mode

        elif action == "load_slides":
            self._slides.load_dialog()
            self._toast.show("Opening slides folder â€¦")

        elif action == "slide_annotate":
            self._state.slide_annotate = not self._state.slide_annotate
            self._toast.show(f"Annotation {'ON' if self._state.slide_annotate else 'OFF'}")

        elif action == "clear_annotation":
            if self._state.slide_mode:
                idx = self._slides.current_index
                self._slides._annotations.pop(idx, None)
                self._toast.show("Annotation cleared")

    # â”€â”€ Gesture change â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _on_gesture_change(self, gesture: Gesture):
        msgs = {
            Gesture.DRAWING:   "âœ Draw",
            Gesture.FIST:      "âœŠ Stop",
            Gesture.TWO:       "âœŒ Black",
            Gesture.THREE:     "ðŸ¤Ÿ Blue",
            Gesture.FOUR:      "ðŸ–– Red",
            Gesture.OPEN_PALM: "ðŸ– Green",
            Gesture.PINCH:     "ðŸ¤ Resize brush",
        }
        if gesture in msgs:
            self._hint.show(msgs[gesture])
        if gesture == Gesture.FIST:
            self._request_pause(
                "fist gesture",
                commit_shape=True,
                disable_tracking=False,
                toast="✊ Drawing paused",
            )

    # â”€â”€ Keyboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _handle_keys(self, key: int, frame: np.ndarray) -> bool:
        if key in (ord('q'), ord('Q')):
            return True
        elif key in (ord('s'), ord('S')):
            self._save_current_frame(frame, source="keyboard")
        elif key in (ord('t'), ord('T')):
            path = self._canvas.save_transparent(self._state.username)
            self._toast.show("Transparent PNG saved âœ“")
        elif key in (ord('a'), ord('A')):
            if self._uploader:
                enabled = self._uploader.toggle_auto_capture()
                self._state.auto_capture_enabled = enabled
                mode = "ON" if enabled else "OFF"
                self._toast.show(f"Auto-capture {mode}")
            else:
                self._toast.show("Auto-capture unavailable (set API URL + JWT token)")
        elif key == ord('['):
            self._state.auto_capture_interval_sec = max(1.0, self._state.auto_capture_interval_sec - 1.0)
            if self._uploader:
                self._uploader.set_auto_capture_interval(self._state.auto_capture_interval_sec)
            self._toast.show(f"Auto interval {self._state.auto_capture_interval_sec:.0f}s")
        elif key == ord(']'):
            self._state.auto_capture_interval_sec += 1.0
            if self._uploader:
                self._uploader.set_auto_capture_interval(self._state.auto_capture_interval_sec)
            self._toast.show(f"Auto interval {self._state.auto_capture_interval_sec:.0f}s")
        elif key in (ord('m'), ord('M')):
            self._state.mirror_mode = not self._state.mirror_mode
            self._toast.show(f"Mirror {'ON' if self._state.mirror_mode else 'OFF'}")
        elif key in (ord('l'), ord('L')):
            self._state.show_landmarks = not self._state.show_landmarks
        elif key in (ord('u'), ord('U')):
            if self._canvas.undo(): self._toast.show("â†© Undo")
        elif key in (ord('r'), ord('R')):
            if self._canvas.redo(): self._toast.show("â†ª Redo")
        elif key in (ord('+'), ord('=')):
            self._brush.adjust(2); self._state.thickness = self._brush.thickness
            self._toast.show(f"Brush {self._state.thickness}px")
        elif key in (ord('-'), ord('_')):
            self._brush.adjust(-2); self._state.thickness = self._brush.thickness
            self._toast.show(f"Brush {self._state.thickness}px")
        elif key in (ord('v'), ord('V')):
            self._toggle_voice()
        elif key in (ord('g'), ord('G')):
            self._toggle_grid()
        elif key in (ord('p'), ord('P')):
            self._state.slide_mode = not self._state.slide_mode
            self._toast.show(f"{'Presentation' if self._state.slide_mode else 'Draw'} mode")
        elif key in (ord('i'), ord('I')):
            self._import_image()
        elif key in (ord('o'), ord('O')):
            self._slides.load_dialog()
            self._toast.show("Opening slides folder â€¦")
        elif key == 27:  # ESC
            self._state.shape_mode = False
            self._shapes.cancel()
            if self._state.drawing_state == DrawingState.PAUSED:
                self._resume_from_pause("keyboard escape")
            else:
                self._state.force_stop = False
                self._state.set_drawing_state(DrawingState.IDLE, "escape reset")
        return False

    def _save_current_frame(self, frame: np.ndarray, source: str = "manual") -> None:
        path = self._canvas.save(frame, self._state.username)
        self._toast.show("Saved âœ“")
        print(f"[INFO] Saved -> {path} ({source})")
        self._queue_remote_frame(frame, source)

    def _queue_remote_frame(self, frame: np.ndarray, source: str) -> None:
        if not self._uploader or not self._remote_session_started:
            return
        brush_mode = "eraser" if self._state.eraser_mode else f"brush_{self._state.thickness}px"
        shape_mode = self._state.active_shape if self._state.shape_mode else "free_draw"
        accepted = self._uploader.enqueue_frame(frame, brush_mode=f"{brush_mode}:{source}", shape_mode=shape_mode)
        if not accepted:
            print("[UPLOAD] Queue full. Dropping frame upload.")

    def _maybe_auto_capture(self, frame: np.ndarray) -> None:
        if not self._uploader or not self._remote_session_started:
            return
        if not self._state.auto_capture_enabled:
            return
        self._uploader.set_auto_capture_interval(self._state.auto_capture_interval_sec)
        if not self._uploader.should_auto_capture_now():
            return

        brush_mode = "eraser" if self._state.eraser_mode else f"brush_{self._state.thickness}px"
        shape_mode = self._state.active_shape if self._state.shape_mode else "free_draw"
        accepted = self._uploader.enqueue_frame(frame, brush_mode=f"{brush_mode}:auto", shape_mode=shape_mode)
        if not accepted:
            print("[UPLOAD] Auto-capture skipped (queue busy).")

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _toggle_voice(self):
        if not self._voice.available:
            self._toast.show("Voice unavailable â€” install SpeechRecognition + PyAudio")
            return
        self._voice_active        = not self._voice_active
        self._state.voice_enabled = self._voice_active
        self._toast.show(f"ðŸŽ™ Voice {'ON' if self._voice_active else 'OFF'}")

    def _toggle_grid(self):
        modes = ["none", "grid", "ruled"]
        self._state.bg_mode = modes[(modes.index(self._state.bg_mode)+1) % len(modes)]
        self._canvas.set_bg_mode(self._state.bg_mode)
        self._toast.show(f"Background: {self._state.bg_mode}")

    def _import_image(self):
        import threading, os
        def _pick():
            try:
                import tkinter as tk
                from tkinter import filedialog
                import cv2 as _cv2
                root = tk.Tk(); root.withdraw()
                root.attributes("-topmost", True)
                path = filedialog.askopenfilename(
                    title="Import Image",
                    filetypes=[("Images","*.png *.jpg *.jpeg *.bmp *.webp"),("All","*.*")]
                )
                root.destroy()
                if path and os.path.isfile(path):
                    img = _cv2.imread(path, _cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        h,w = img.shape[:2]
                        max_w = int(DISPLAY_WIDTH*0.55)
                        ratio = min(max_w/max(w,1), 1.0)
                        nw,nh = int(w*ratio), int(h*ratio)
                        img   = _cv2.resize(img,(nw,nh))
                        if img.shape[2]==3:
                            img = _cv2.cvtColor(img,_cv2.COLOR_BGR2BGRA)
                        x = (DISPLAY_WIDTH-nw)//2
                        y = (DISPLAY_HEIGHT-nh)//2
                        self._canvas.push_undo()
                        self._canvas.blit_image(img, x, y)
                        print(f"[INFO] Image imported: {nw}Ã—{nh}")
            except Exception as e:
                print(f"[IMPORT] Error: {e}")
        threading.Thread(target=_pick, daemon=True).start()
        self._toast.show("ðŸ–¼ Opening image picker â€¦")

    def _draw_status(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        if self._state.slide_mode:
            mode = f"SLIDES  {self._slides.current_index+1}/{max(self._slides.count,1)}"
        elif self._state.drawing_state == DrawingState.PAUSED:
            mode = "â–  STOPPED"
        elif self._state.eraser_mode:
            mode = "âŒ« ERASE"
        elif self._state.shape_mode:
            mode = f"â—ˆ {self._shapes.active_shape.upper()}"
        else:
            mode = "âœ DRAW"
        state_tag = self._state.drawing_state
        bg_tag = f"  bg:{self._state.bg_mode}" if self._state.bg_mode != "none" else ""
        text   = f"{mode} [{state_tag}]{bg_tag}"
        font,scale = cv2.FONT_HERSHEY_SIMPLEX, 0.40
        (tw,_),_   = cv2.getTextSize(text,font,scale,1)
        cv2.putText(frame,text,(w-tw-10,h-10),font,scale,UI_MUTED,1,cv2.LINE_AA)

    # â”€â”€ Shutdown â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _shutdown(self):
        print("[INFO] Shutting down ...")
        avg_fps = (self._fps_sum / self._fps_samples) if self._fps_samples else None
        if self._uploader:
            self._uploader.stop(avg_fps=avg_fps)
        self._det_thread.stop()
        self._voice.stop()
        self._detector.release()
        self._cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Goodbye!")

