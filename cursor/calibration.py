"""
Calibration webcam <-> écran (spec section 11).

Convertit une position normalisée (0..1, repère webcam) en position
relative (0..1) dans une "zone active" configurable : ne pas obliger
l'utilisateur à approcher l'index des bords physiques de l'image pour
atteindre les bords de l'écran.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Calibration:
    # Zone active dans le cadre webcam, coordonnées normalisées 0..1
    active_left: float = 0.15
    active_top: float = 0.15
    active_right: float = 0.85
    active_bottom: float = 0.85

    def to_relative(self, x_norm: float, y_norm: float) -> Tuple[float, float]:
        """Convertit un point (repère webcam) en position relative 0..1
        dans la zone active, sans clamp (le clamp est fait par l'appelant
        après application de la sensibilité)."""
        width = self.active_right - self.active_left
        height = self.active_bottom - self.active_top

        x_rel = (x_norm - self.active_left) / width if width > 0 else 0.0
        y_rel = (y_norm - self.active_top) / height if height > 0 else 0.0
        return x_rel, y_rel
