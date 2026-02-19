"""
config.py — AntiGravity AirCanvas 4.0
All tunable constants. Nothing hardcoded elsewhere.
"""

# ── Camera ────────────────────────────────────────────────────────────────────
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency at runtime
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

CAMERA_INDEX     = 0
DISPLAY_WIDTH    = 1280
DISPLAY_HEIGHT   = 720
DETECT_WIDTH     = 512
DETECT_HEIGHT    = 288
TARGET_FPS       = 120
CAMERA_BUFFER_SIZE = 1
CAMERA_FOURCC      = "MJPG"

# ── MediaPipe ─────────────────────────────────────────────────────────────────
MAX_NUM_HANDS        = 2
DETECTION_CONFIDENCE = 0.70
TRACKING_CONFIDENCE  = 0.65
MODEL_FILENAME       = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)

# ── Gesture ───────────────────────────────────────────────────────────────────
DEBOUNCE_DELAY        = 0.10
CLEAR_HOLD_DURATION   = 0.9
PINCH_THRESHOLD       = 0.07
SWIPE_VELOCITY_THRESH = 380
SWIPE_WINDOW          = 0.28
EMA_ALPHA             = 0.40

# Toolbar hover-to-activate threshold
HOVER_ACTIVATE_SEC    = 0.14

# ── Depth guard ───────────────────────────────────────────────────────────────
DEPTH_MODE           = "z_axis"
DEPTH_THRESHOLD      = 0.06
PINCH_DRAW_THRESHOLD = 0.09

# ── Brush ─────────────────────────────────────────────────────────────────────
DEFAULT_THICKNESS    = 5
MIN_THICKNESS        = 1
MAX_THICKNESS        = 50
ERASER_THICKNESS     = 55
SPEED_BRUSH_ENABLED  = os.getenv("SPEED_BRUSH_ENABLED", "0").strip() in ("1", "true", "True")
# Keep brush width stable by default. Set SPEED_BRUSH_ENABLED=1 to re-enable dynamic sizing.
SPEED_MIN_FACTOR     = 0.6      # min multiplier at high speed
SPEED_MAX_FACTOR     = 1.4      # max multiplier at low speed

# ── Kalman filter ─────────────────────────────────────────────────────────────
KALMAN_PROCESS_NOISE = 2e-3
KALMAN_MEASURE_NOISE = 6e-3

# ── Canvas ────────────────────────────────────────────────────────────────────
CANVAS_ALPHA     = 0.90
MAX_UNDO_STEPS   = 40
GRID_CELL_SIZE   = 40          # pixels per grid cell
SNAP_THRESHOLD   = 14          # px snap-to-grid tolerance

# ── Shape ─────────────────────────────────────────────────────────────────────
SHAPE_HOLD_SECONDS    = 0.32
SHAPE_PREVIEW_ALPHA   = 0.55
SHAPE_EMA_ALPHA       = 0.35
SHAPE_MIN_MOVE_PX     = 3
SHAPE_MIN_SIZE_PX     = 10
SHAPE_STILL_RADIUS_PX = 20

# ── Colours (BGR) ─────────────────────────────────────────────────────────────
COL_GREEN   = (30,  200,  60)
COL_RED     = (30,   40, 220)
COL_BLUE    = (220,  90,  20)
COL_BLACK   = (15,   15,  15)
COL_YELLOW  = (0,   210, 220)
COL_WHITE   = (240, 240, 240)
COL_PURPLE  = (180,  40, 160)
COL_ORANGE  = (0,   140, 240)

PALETTE = [
    ("Green",  COL_GREEN,  "color_green"),
    ("Red",    COL_RED,    "color_red"),
    ("Blue",   COL_BLUE,   "color_blue"),
    ("Black",  COL_BLACK,  "color_black"),
    ("Yellow", COL_YELLOW, "color_yellow"),
    ("Purple", COL_PURPLE, "color_purple"),
    ("Orange", COL_ORANGE, "color_orange"),
]
GESTURE_COLOR_MAP = {5: COL_GREEN, 4: COL_RED, 3: COL_BLUE, 2: COL_BLACK}

# ── UI ────────────────────────────────────────────────────────────────────────
TOOLBAR_H     = 68
BTN_W         = 46
BTN_H         = 42
BTN_GAP       = 8

# Minimal dark palette
UI_BG         = (10,  10,  14)
UI_PANEL      = (18,  18,  24)
UI_BORDER     = (38,  36,  52)
UI_ACCENT     = (100, 80, 240)   # indigo
UI_ACCENT2    = (60, 180, 255)   # cyan
UI_HIGHLIGHT  = (255,200,  60)   # amber
UI_TEXT       = (200, 198, 215)
UI_MUTED      = (80,  78,  95)
UI_DANGER     = (200,  55,  45)

# ── Landmarks ─────────────────────────────────────────────────────────────────
WRIST      = 0
THUMB_TIP  = 4;  THUMB_IP   = 3
INDEX_TIP  = 8;  INDEX_PIP  = 6;  INDEX_MCP  = 5
MIDDLE_TIP = 12; MIDDLE_PIP = 10; MIDDLE_MCP = 9
RING_TIP   = 16; RING_PIP   = 14; RING_MCP   = 13
PINKY_TIP  = 20; PINKY_PIP  = 18; PINKY_MCP  = 17

# ── Voice ─────────────────────────────────────────────────────────────────────
VOICE_ENABLED          = True
VOICE_LANGUAGE         = "en-US"
VOICE_ENERGY_THRESHOLD = 280
VOICE_PAUSE_THRESHOLD  = 0.5
VOICE_PHRASE_LIMIT     = 5.0
VOICE_BRUSH_STEP       = 5
VOICE_TOAST_DURATION   = 2.0

# ── Slide / Presentation ──────────────────────────────────────────────────────
SLIDE_DIR            = "slides"
SLIDE_EXTENSIONS     = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
LASER_COLOR          = (0, 60, 255)     # BGR red laser dot
LASER_RADIUS         = 12

# ── I/O ───────────────────────────────────────────────────────────────────────
SAVE_DIR     = "saves"
SAVE_PREFIX  = "aircanvas4"
WINDOW_TITLE = "AntiGravity AirCanvas 4.0"

# Remote backend integration
API_BASE_URL = os.getenv("API_BASE_URL", "").strip()
AIRCANVAS_API_BASE_URL = (os.getenv("AIRCANVAS_API_BASE_URL", "").strip() or API_BASE_URL)
AIRCANVAS_JWT_TOKEN = os.getenv("AIRCANVAS_JWT_TOKEN", "").strip()
AIRCANVAS_API_TIMEOUT_SEC = float(os.getenv("AIRCANVAS_API_TIMEOUT_SEC", "8"))

# Frame upload worker
FRAME_UPLOAD_QUEUE_SIZE = int(os.getenv("FRAME_UPLOAD_QUEUE_SIZE", "32"))
FRAME_UPLOAD_RETRY_MAX = int(os.getenv("FRAME_UPLOAD_RETRY_MAX", "3"))
FRAME_UPLOAD_RETRY_BACKOFF_SEC = float(os.getenv("FRAME_UPLOAD_RETRY_BACKOFF_SEC", "1.4"))
FRAME_PNG_COMPRESSION = int(os.getenv("FRAME_PNG_COMPRESSION", "3"))
FRAME_THUMB_MAX_WIDTH = int(os.getenv("FRAME_THUMB_MAX_WIDTH", "420"))
FRAME_THUMB_JPEG_QUALITY = int(os.getenv("FRAME_THUMB_JPEG_QUALITY", "76"))
FRAME_UPLOAD_LOCAL_FALLBACK = os.getenv("FRAME_UPLOAD_LOCAL_FALLBACK", "1").strip() in ("1", "true", "True")
FRAME_UPLOAD_FALLBACK_DIR = (os.getenv("FRAME_UPLOAD_FALLBACK_DIR", "").strip() or SAVE_DIR)

# Optional auto-capture mode
AUTO_CAPTURE_DEFAULT_ENABLED = os.getenv("AUTO_CAPTURE_DEFAULT_ENABLED", "0").strip() in ("1", "true", "True")
AUTO_CAPTURE_INTERVAL_SEC = float(os.getenv("AUTO_CAPTURE_INTERVAL_SEC", "10"))
