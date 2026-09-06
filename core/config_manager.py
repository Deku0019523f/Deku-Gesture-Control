"""
Chargement/sauvegarde des fichiers de configuration JSON (spec section 19,
20, 21, 26) : settings.json, gestures.json, profiles.json.

Ne code jamais en dur les paramètres qui doivent être configurables (spec
section 26) : ce module est le point d'entrée unique pour lire/écrire ces
trois fichiers.
"""
from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict

from core.constants import GESTURES_FILE, PROFILES_FILE, SETTINGS_FILE

logger = logging.getLogger("deku.config")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "camera": {"device": 0, "width": 1280, "height": 720, "fps": 30},
    "cursor": {"sensitivity": 1.0, "smoothing": 0.5, "dead_zone": 0.02},
    "gestures": {"confidence_threshold": 0.6, "min_hold_duration": 0.05, "click_cooldown": 0.3},
    "interface": {"theme": "dark"},
}

# Mapping geste -> action (spec section 13). "pinch"/"pinch_double"/
# "pinch_hold_and_move" pilotent le pointeur (clic gauche/double-clic/drag)
# et ne sont pas réassignables : c'est le mécanisme de pointage de base.
# "two_fingers" et les swipes sont réassignables depuis l'onglet Gestes.
DEFAULT_GESTURES_MAPPING: Dict[str, str] = {
    "pinch": "left_click",
    "pinch_double": "double_click",
    "pinch_hold_and_move": "drag",
    "two_fingers": "right_click",
    "two_fingers_vertical": "scroll",
    "swipe_left": "previous",
    "swipe_right": "next",
    "swipe_up": "mission_control",
    "swipe_down": "show_desktop",
}

DEFAULT_PROFILES: Dict[str, Any] = {
    "default": {
        "description": "Navigation normale",
        "settings": {},
        "gestures": {},
    },
    "gaming": {
        "description": "Curseur plus sensible, moins de lissage",
        "settings": {"cursor": {"sensitivity": 1.4, "smoothing": 0.3}},
        "gestures": {},
    },
    "presentation": {
        "description": "Swipes pour changer de diapositive",
        "settings": {},
        "gestures": {"swipe_left": "previous", "swipe_right": "next"},
    },
    "browsing": {
        "description": "Navigation web précédent/suivant",
        "settings": {},
        "gestures": {"swipe_left": "previous", "swipe_right": "next", "swipe_up": "none", "swipe_down": "none"},
    },
}


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    """Charge un fichier JSON, le crée avec les valeurs par défaut s'il
    n'existe pas encore, et retombe sur les valeurs par défaut s'il est
    corrompu (jamais de crash au démarrage à cause d'une config invalide)."""
    if not path.exists():
        save_json(path, default)
        return copy.deepcopy(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Configuration invalide (%s), retour aux valeurs par défaut : %s", path, exc)
        return copy.deepcopy(default)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_settings() -> Dict[str, Any]:
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]) -> None:
    save_json(SETTINGS_FILE, settings)


def load_gestures_mapping() -> Dict[str, str]:
    return load_json(GESTURES_FILE, DEFAULT_GESTURES_MAPPING)


def save_gestures_mapping(mapping: Dict[str, str]) -> None:
    save_json(GESTURES_FILE, mapping)


def load_profiles() -> Dict[str, Any]:
    return load_json(PROFILES_FILE, DEFAULT_PROFILES)


def save_profiles(profiles: Dict[str, Any]) -> None:
    save_json(PROFILES_FILE, profiles)


def apply_profile_overrides(settings: Dict[str, Any], gestures: Dict[str, str], profile: Dict[str, Any]) -> None:
    """Applique en place les surcharges d'un profil sur settings/gestures
    (spec section 21). Fusion superficielle par section, suffisante pour
    les quelques clés concernées."""
    for section, values in profile.get("settings", {}).items():
        settings.setdefault(section, {}).update(values)
    gestures.update(profile.get("gestures", {}))
