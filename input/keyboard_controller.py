"""
Contrôle clavier (spec section 15) : associe des gestes (essentiellement
les swipes) à des raccourcis clavier configurables.

Le mapping geste -> nom d'action vit dans config/gestures.json (édité
depuis l'onglet Gestes en Phase 8) ; ce module ne connaît que les noms
d'action -> combinaisons de touches.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

import pyautogui

logger = logging.getLogger("deku.input.keyboard")

# Actions nommées disponibles pour le mapping des swipes (spec section 15).
NAMED_ACTION_SHORTCUTS: Dict[str, Optional[Tuple[str, ...]]] = {
    "previous": ("alt", "left"),
    "next": ("alt", "right"),
    "mission_control": ("ctrl", "up"),
    "show_desktop": ("win", "d"),
    "none": None,
}


class KeyboardController:
    """Fine couche au-dessus de PyAutoGUI pour les raccourcis clavier."""

    def trigger_named(self, action_name: str) -> bool:
        """Déclenche le raccourci associé à un nom d'action (spec section
        13/15). Retourne True si un raccourci a bien été envoyé."""
        combo = NAMED_ACTION_SHORTCUTS.get(action_name)
        if not combo:
            return False
        logger.info("Raccourci clavier : %s -> %s", action_name, "+".join(combo))
        pyautogui.hotkey(*combo)
        return True

    def press_key(self, key: str) -> None:
        pyautogui.press(key)

    def hotkey(self, *keys: str) -> None:
        pyautogui.hotkey(*keys)
