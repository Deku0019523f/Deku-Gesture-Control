"""
Lissage du curseur (spec section 12) : le curseur ne doit pas trembler.

Deux stratégies configurables via smoothing_strength :
- moyenne glissante ;
- filtre exponentiel (par défaut : plus réactif, moins de latence).
"""
from __future__ import annotations

from collections import deque
from typing import Deque, Optional, Tuple


class MovingAverageSmoother:
    """Moyenne glissante sur les N dernières positions."""

    def __init__(self, window_size: int = 5):
        self.window_size = max(1, window_size)
        self._history: Deque[Tuple[float, float]] = deque(maxlen=self.window_size)

    def smooth(self, x: float, y: float) -> Tuple[float, float]:
        self._history.append((x, y))
        avg_x = sum(p[0] for p in self._history) / len(self._history)
        avg_y = sum(p[1] for p in self._history) / len(self._history)
        return avg_x, avg_y

    def reset(self) -> None:
        self._history.clear()


class ExponentialSmoother:
    """Filtre exponentiel.

    smoothing_strength dans [0, 1[ : 0 = aucun lissage (suit la main
    instantanément), proche de 1 = très lissé mais plus de latence.
    """

    def __init__(self, smoothing_strength: float = 0.5):
        self.smoothing_strength = min(max(smoothing_strength, 0.0), 0.99)
        self._last: Optional[Tuple[float, float]] = None

    def smooth(self, x: float, y: float) -> Tuple[float, float]:
        if self._last is None:
            self._last = (x, y)
            return self._last

        alpha = 1.0 - self.smoothing_strength
        new_x = self._last[0] + alpha * (x - self._last[0])
        new_y = self._last[1] + alpha * (y - self._last[1])
        self._last = (new_x, new_y)
        return self._last

    def reset(self) -> None:
        self._last = None


def create_smoother(strength: float = 0.5, mode: str = "exponential"):
    """Fabrique un lisseur configurable (spec section 12)."""
    if mode == "moving_average":
        window = max(1, int(2 + strength * 10))  # 0 -> 2 frames, 1 -> 12 frames
        return MovingAverageSmoother(window_size=window)
    return ExponentialSmoother(smoothing_strength=strength)
