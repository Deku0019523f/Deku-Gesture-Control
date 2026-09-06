"""
Actions système (spec section 16) : raccourci clavier global pour
activer/désactiver le contrôle gestuel (spec section 17). Aucune action
système dangereuse par défaut.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from pynput import keyboard as pynput_keyboard

logger = logging.getLogger("deku.input.system")

DEFAULT_PAUSE_HOTKEY = "<ctrl>+<alt>+p"


class SystemController:
    """Gère le raccourci clavier global de pause/reprise.

    Fonctionne même si la fenêtre de l'application n'a pas le focus, via
    un listener pynput dédié (thread séparé, géré par pynput lui-même).
    """

    def __init__(self, on_toggle_pause: Callable[[], None], hotkey: str = DEFAULT_PAUSE_HOTKEY):
        self._on_toggle_pause = on_toggle_pause
        self._hotkey_str = hotkey
        self._listener: Optional[pynput_keyboard.GlobalHotKeys] = None

    def start(self) -> None:
        try:
            self._listener = pynput_keyboard.GlobalHotKeys({self._hotkey_str: self._on_toggle_pause})
            self._listener.start()
            logger.info("Raccourci global de pause actif : %s", self._hotkey_str)
        except Exception as exc:
            logger.warning("Impossible d'activer le raccourci clavier global (%s) : %s", self._hotkey_str, exc)
            self._listener = None

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
