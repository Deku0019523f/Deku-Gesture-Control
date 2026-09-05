"""
Geste "deux doigts" (index + majeur tendus, annulaire + auriculaire
repliés) : utilisé pour le clic droit (spec section 8 — "utiliser un
geste distinct, par exemple ✌️").
"""
from __future__ import annotations

from typing import Dict, Sequence

from gestures.gesture_state import BinaryGestureState, DebouncedBinaryGesture
from vision import hand_geometry as geo

_REQUIRED_POINTS = {
    "index_mcp", "index_pip", "index_tip",
    "middle_mcp", "middle_pip", "middle_tip",
    "ring_mcp", "ring_pip", "ring_tip",
    "pinky_mcp", "pinky_pip", "pinky_tip",
}


def _is_two_fingers(points: Dict[str, Sequence[float]]) -> bool:
    return (
        geo.is_finger_extended(points, "index")
        and geo.is_finger_extended(points, "middle")
        and not geo.is_finger_extended(points, "ring")
        and not geo.is_finger_extended(points, "pinky")
    )


class TwoFingersGesture:
    """Détecte le geste deux-doigts, filtré via DebouncedBinaryGesture."""

    name = "TWO_FINGERS"

    def __init__(self, **debounce_kwargs):
        debounce_kwargs.setdefault("cooldown_duration", 0.4)
        self._debouncer = DebouncedBinaryGesture(**debounce_kwargs)

    def update(self, points_norm: Dict[str, Sequence[float]]) -> BinaryGestureState:
        if _REQUIRED_POINTS.issubset(points_norm.keys()):
            raw = _is_two_fingers(points_norm)
        else:
            raw = False
        return self._debouncer.update(raw)

    @property
    def state(self) -> BinaryGestureState:
        return self._debouncer.state
