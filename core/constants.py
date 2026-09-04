"""
Constantes globales pour Deku Gesture Control.

Centraliser ces valeurs ici évite de coder en dur des paramètres
qui doivent rester configurables (cf. spec section 26/32).
"""
from pathlib import Path

APP_NAME = "Deku Gesture Control"
APP_VERSION = "0.1.0"

# --- Répertoires ---------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ASSETS_DIR = ROOT_DIR / "assets"
LOGS_DIR = ROOT_DIR / "logs"

SETTINGS_FILE = CONFIG_DIR / "settings.json"
GESTURES_FILE = CONFIG_DIR / "gestures.json"
PROFILES_FILE = CONFIG_DIR / "profiles.json"

LOGO_PATH = ASSETS_DIR / "logo.png"

# --- Caméra (valeurs par défaut, surchargées par config/settings.json) --
DEFAULT_CAMERA_INDEX = 0
DEFAULT_CAMERA_WIDTH = 1280
DEFAULT_CAMERA_HEIGHT = 720
DEFAULT_CAMERA_FPS = 30
MAX_CAMERA_PROBE_INDEX = 5  # nombre d'index testés lors de la détection des webcams

# --- Interface -------------------------------------------------------------
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 650

# --- Thème (couleurs reprises du logo Deku Gesture Control) -------------
COLOR_BG = "#121417"
COLOR_BG_PANEL = "#1b1e23"
COLOR_ACCENT = "#22e0a8"
COLOR_ACCENT_DARK = "#189a73"
COLOR_TEXT = "#f2f2f2"
COLOR_TEXT_MUTED = "#9aa0a6"
COLOR_ERROR = "#ff5c5c"
COLOR_WARNING = "#ffb84d"
