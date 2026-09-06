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

    # --- Phase 5 ---
    def left_click(self) -> None:
        pyautogui.click(button="left")

    def right_click(self) -> None:
        pyautogui.click(button="right")

    def double_click(self) -> None:
        pyautogui.doubleClick()

    def mouse_down(self) -> None:
        pyautogui.mouseDown(button="left")

    def mouse_up(self) -> None:
        pyautogui.mouseUp(button="left")

    def drag_start(self) -> None:
        self.mouse_down()

    def drag_move(self, x: float, y: float) -> None:
        self.move(x, y)

    def drag_end(self) -> None:
        self.mouse_up()

    # --- Phase 6 ---
    def scroll(self, amount: int) -> None:
        if amount:
            pyautogui.scroll(amount)
