"""
Constantes globales pour Deku Gesture Control.

Les couleurs et polices suivent la charte graphique officielle du projet
(fournie par l'utilisateur) : palette teal/navy, typographies Poppins
(titres) et Inter (texte).
"""
from pathlib import Path

APP_NAME = "Deku Gesture Control"
APP_VERSION = "1.0.0"
APP_TAGLINE = "CONTRÔLEZ. GESTICULEZ. ACCOMPLISSEZ."

# --- Répertoires ---------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ASSETS_DIR = ROOT_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
LOGS_DIR = ROOT_DIR / "logs"

SETTINGS_FILE = CONFIG_DIR / "settings.json"
GESTURES_FILE = CONFIG_DIR / "gestures.json"
PROFILES_FILE = CONFIG_DIR / "profiles.json"

LOGO_PATH = ASSETS_DIR / "logo.png"
ICON_ICO_PATH = ASSETS_DIR / "icon.ico"

# --- Caméra (valeurs par défaut, surchargées par config/settings.json) --
DEFAULT_CAMERA_INDEX = 0
DEFAULT_CAMERA_WIDTH = 1280
DEFAULT_CAMERA_HEIGHT = 720
DEFAULT_CAMERA_FPS = 30
MAX_CAMERA_PROBE_INDEX = 5

# --- Interface -------------------------------------------------------------
WINDOW_MIN_WIDTH = 980
WINDOW_MIN_HEIGHT = 700

# --- Typographie (charte graphique : Poppins / Inter) --------------------
FONT_HEADING = "Poppins"
FONT_BODY = "Inter"
FONT_FILES = [
    "Poppins-Bold.ttf",
    "Poppins-SemiBold.ttf",
    "Poppins-Regular.ttf",
    "Inter-Variable.ttf",
]

# --- Palette (charte graphique officielle) --------------------------------
BRAND_ACCENT = "#00E6B8"       # teal primaire
BRAND_ACCENT_DARK = "#00B4A6"  # teal secondaire (hover/pressed)
BRAND_NAVY_DARK = "#0D1117"    # fond sombre
BRAND_NAVY_PANEL = "#1B212B"   # panneaux/cartes sombres
BRAND_LIGHT_BG = "#E6ECF1"     # fond clair
BRAND_WHITE = "#FFFFFF"

# Couleurs sémantiques des badges de statut (charte graphique, section chips)
STATUS_ACTIVE = "#2ECC71"   # ACTIF
STATUS_PAUSED = "#F5A623"   # EN PAUSE
STATUS_INFO = "#3B82F6"     # INFO
STATUS_ERROR = "#E5484D"    # DÉSACTIVÉ / ERREUR

THEMES = {
    "dark": {
        "bg": BRAND_NAVY_DARK,
        "bg_panel": BRAND_NAVY_PANEL,
        "border": "#232B36",
        "text": BRAND_WHITE,
        "text_muted": "#8A94A6",
        "accent": BRAND_ACCENT,
        "accent_dark": BRAND_ACCENT_DARK,
        "accent_text": "#06110d",  # texte sur fond accent (contraste)
    },
    "light": {
        "bg": BRAND_LIGHT_BG,
        "bg_panel": BRAND_WHITE,
        "border": "#D3DAE1",
        "text": BRAND_NAVY_DARK,
        "text_muted": "#5A6472",
        "accent": BRAND_ACCENT,
        "accent_dark": BRAND_ACCENT_DARK,
        "accent_text": "#06110d",
    },
}

DEFAULT_THEME = "dark"

# Alias conservés pour compatibilité avec le code existant (thème sombre).
COLOR_BG = THEMES["dark"]["bg"]
COLOR_BG_PANEL = THEMES["dark"]["bg_panel"]
COLOR_ACCENT = THEMES["dark"]["accent"]
COLOR_ACCENT_DARK = THEMES["dark"]["accent_dark"]
COLOR_TEXT = THEMES["dark"]["text"]
COLOR_TEXT_MUTED = THEMES["dark"]["text_muted"]
COLOR_ERROR = STATUS_ERROR
COLOR_WARNING = STATUS_PAUSED
