"""
Geste PINCH : pouce + index rapprochés (spec section 8).
"""
from __future__ import annotations

from typing import Dict, Sequence

from gestures.gesture_state import BinaryGestureState, DebouncedBinaryGesture
from vision import hand_geometry as geo

DEFAULT_PINCH_THRESHOLD = geo.DEFAULT_PINCH_THRESHOLD


class PinchGesture:
    """Détecte le pinch et filtre les faux positifs via DebouncedBinaryGesture."""

    name = "PINCH"

    def __init__(self, threshold: float = DEFAULT_PINCH_THRESHOLD, **debounce_kwargs):
        self.threshold = threshold
        self._debouncer = DebouncedBinaryGesture(**debounce_kwargs)

    def update(self, points_norm: Dict[str, Sequence[float]]) -> BinaryGestureState:
        """À appeler une fois par frame avec les points normalisés de la main
        (ou un dict vide si aucune main n'est détectée sur cette frame)."""
        if "thumb_tip" in points_norm and "index_tip" in points_norm:
            raw = geo.is_pinch(points_norm, threshold=self.threshold)
        else:
            raw = False
        return self._debouncer.update(raw)

    @property
    def state(self) -> BinaryGestureState:
        return self._debouncer.state
