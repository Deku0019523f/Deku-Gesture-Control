"""
Geste de swipe (spec section 8 : SWIPE_LEFT/RIGHT/UP/DOWN) : main grande
ouverte (5 doigts tendus) déplacée rapidement dans une direction.

Le déclenchement exige une main ouverte pour le distinguer du simple
pointage (index seul) et des gestes pinch/deux-doigts. C'est la même
forme de main que le mode pause (spec section 17) — les deux sont
différenciés par la vitesse plutôt que par la forme : immobile -> pause,
rapide -> swipe.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from vision import hand_geometry as geo

SWIPE_MIN_SPEED = 1.4          # unités normalisées/seconde
SWIPE_COOLDOWN = 0.6           # secondes avant de pouvoir redéclencher
OPEN_HAND_MIN_OPENNESS = 0.8   # proportion de doigts tendus requise


class SwipeGesture:
    def __init__(
        self,
        min_speed: float = SWIPE_MIN_SPEED,
        cooldown: float = SWIPE_COOLDOWN,
        min_openness: float = OPEN_HAND_MIN_OPENNESS,
        history_size: int = 5,
    ):
        self.min_speed = min_speed
        self.cooldown = cooldown
        self.min_openness = min_openness
        self._velocity = geo.VelocityTracker(history_size=history_size)
        self._last_trigger_time: Optional[float] = None

    def update(self, points_norm: Dict[str, Sequence[float]], timestamp: float) -> Optional[str]:
        """Retourne "SWIPE_LEFT"/"SWIPE_RIGHT"/"SWIPE_UP"/"SWIPE_DOWN" ou None."""
        if "wrist" not in points_norm:
            self._velocity.reset()
            return None

        if geo.hand_openness(points_norm) < self.min_openness:
            self._velocity.reset()
            return None

        self._velocity.update(points_norm["wrist"], timestamp)

        if self._last_trigger_time is not None and (timestamp - self._last_trigger_time) < self.cooldown:
            return None

        vx, vy = self._velocity.get_velocity()
        speed = (vx ** 2 + vy ** 2) ** 0.5
        if speed < self.min_speed:
            return None

        direction = self._velocity.get_direction(min_speed=self.min_speed)
        if direction == "none":
            return None

        self._last_trigger_time = timestamp
        self._velocity.reset()
        return f"SWIPE_{direction.upper()}"
