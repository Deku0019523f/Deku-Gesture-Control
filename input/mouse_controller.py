"""
Contrôle souris (spec section 14).

Phase 4 : déplacement du curseur (move) uniquement. Les clics, le
maintien et le drag & drop sont réservés à la Phase 5, le scroll à la
Phase 6 — ils sont déclarés ici mais lèvent NotImplementedError pour
qu'un appel prématuré échoue explicitement plutôt que silencieusement.
"""
from __future__ import annotations

import logging
from typing import Tuple

import pyautogui

logger = logging.getLogger("deku.input.mouse")

# Le curseur peut légitimement passer par les coins de l'écran pendant le
# suivi de l'index : on désactive le failsafe de PyAutoGUI qui lèverait
# une exception dans ce cas.
pyautogui.FAILSAFE = False
# Les appels move() sont déjà cadencés par la boucle de capture caméra.
pyautogui.PAUSE = 0


class MouseController:
    """Fine couche au-dessus de PyAutoGUI : le reste du programme ne doit
    jamais importer pyautogui/pynput directement (spec section 14)."""

    def get_screen_size(self) -> Tuple[int, int]:
        return tuple(pyautogui.size())

    def move(self, x: float, y: float) -> None:
        pyautogui.moveTo(int(x), int(y))

    # --- Réservé Phase 5/6 ---
    def left_click(self) -> None:
        raise NotImplementedError("Clic gauche : Phase 5")

    def right_click(self) -> None:
        raise NotImplementedError("Clic droit : Phase 5")

    def double_click(self) -> None:
        raise NotImplementedError("Double-clic : Phase 5")

    def mouse_down(self) -> None:
        raise NotImplementedError("Maintien de clic : Phase 5")

    def mouse_up(self) -> None:
        raise NotImplementedError("Relâchement de clic : Phase 5")

    def scroll(self, amount: int) -> None:
        raise NotImplementedError("Scroll : Phase 6")

    def drag_start(self) -> None:
        raise NotImplementedError("Drag & drop : Phase 5")

    def drag_move(self, x: float, y: float) -> None:
        raise NotImplementedError("Drag & drop : Phase 5")

    def drag_end(self) -> None:
        raise NotImplementedError("Drag & drop : Phase 5")
