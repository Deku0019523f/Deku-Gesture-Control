"""
Mode pause (spec section 17) : main grande ouverte maintenue immobile
~1 seconde bascule le contrôle gestuel en pause (aucune action
souris/clavier tant que la pause est active — voir CameraWorker).

Réutilise la forme "main ouverte" du swipe, différenciée par l'absence de
mouvement plutôt que par la vitesse.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from vision import hand_geometry as geo

HOLD_DURATION = 1.0        # secondes de main ouverte immobile avant de basculer
MIN_OPENNESS = 0.9         # main quasi totalement ouverte


class PauseTrigger:
    def __init__(self, hold_duration: float = HOLD_DURATION, min_openness: float = MIN_OPENNESS):
        self.hold_duration = hold_duration
        self.min_openness = min_openness
        self._hand_open_since: Optional[float] = None
        self._armed = True  # évite un nouveau déclenchement tant que la main n'a pas changé de forme

    def update(self, points_norm: Dict[str, Sequence[float]], timestamp: float) -> bool:
        """Retourne True la frame où le seuil de maintien vient d'être atteint."""
        if not points_norm or geo.hand_openness(points_norm) < self.min_openness:
            self._hand_open_since = None
            self._armed = True
            return False

        if self._hand_open_since is None:
            self._hand_open_since = timestamp
            return False

        if self._armed and (timestamp - self._hand_open_since) >= self.hold_duration:
            self._armed = False
            return True

        return False

    def reset(self) -> None:
        self._hand_open_since = None
        self._armed = True
