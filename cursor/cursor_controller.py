"""
CursorController : transforme la position de l'index détectée par la
webcam en mouvement réel du curseur système (spec section 11).

Pipeline : coordonnées webcam -> calibration -> sensibilité -> lissage ->
zone morte -> souris.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple

from cursor.calibration import Calibration
from cursor.smoothing import create_smoother
from input.mouse_controller import MouseController

logger = logging.getLogger("deku.cursor")


class CursorController:
    def __init__(
        self,
        mouse_controller: Optional[MouseController] = None,
        calibration: Optional[Calibration] = None,
        sensitivity: float = 1.0,
        smoothing_strength: float = 0.5,
        dead_zone: float = 0.02,
    ):
        self._mouse = mouse_controller or MouseController()
        self._calibration = calibration or Calibration()
        self.sensitivity = sensitivity
        self.dead_zone = dead_zone
        self._smoother = create_smoother(strength=smoothing_strength)
        self._last_screen_pos: Optional[Tuple[float, float]] = None

    def update(self, index_x_norm: float, index_y_norm: float) -> Tuple[float, float]:
        """Reçoit la position normalisée de l'index (repère webcam) et
        déplace le curseur système en conséquence. Retourne la position
        écran calculée (utile pour l'affichage/debug)."""
        x_rel, y_rel = self._calibration.to_relative(index_x_norm, index_y_norm)

        # Sensibilité : amplifie/réduit l'écart au centre de la zone active.
        x_rel = 0.5 + (x_rel - 0.5) * self.sensitivity
        y_rel = 0.5 + (y_rel - 0.5) * self.sensitivity
        x_rel = min(max(x_rel, 0.0), 1.0)
        y_rel = min(max(y_rel, 0.0), 1.0)

        screen_w, screen_h = self._mouse.get_screen_size()
        target_x, target_y = x_rel * screen_w, y_rel * screen_h

        smoothed_x, smoothed_y = self._smoother.smooth(target_x, target_y)

        if self._last_screen_pos is not None:
            moved = (
                (smoothed_x - self._last_screen_pos[0]) ** 2
                + (smoothed_y - self._last_screen_pos[1]) ** 2
            ) ** 0.5
            dead_zone_px = self.dead_zone * min(screen_w, screen_h)
            if moved < dead_zone_px:
                return self._last_screen_pos

        self._last_screen_pos = (smoothed_x, smoothed_y)
        self._mouse.move(smoothed_x, smoothed_y)
        return self._last_screen_pos

    def reset(self) -> None:
        self._smoother.reset()
        self._last_screen_pos = None
