"""
Moteur central de reconnaissance de gestes (spec section 8/9).

Phase 3 : détecte le geste PINCH et son état à partir des landmarks de la
main. Aucune action souris/clavier n'est déclenchée ici — le mapping
gestes -> actions arrive en Phase 5+ (spec section 13).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from gestures.gesture_detector import detect_raw_gestures
from gestures.gesture_state import BinaryGestureState
from gestures.gestures.pinch import PinchGesture
from vision.hand_tracker import HandData
from vision.landmark_processor import process_landmarks


@dataclass
class GestureSnapshot:
    """État courant du moteur de gestes, pour affichage/test (Phase 3)."""

    hand_detected: bool
    gesture_name: str
    state_name: str
    confidence: float
    hand_openness: float = 0.0
    index_tip_px: Optional[Tuple[int, int]] = None


class GestureEngine:
    """Traite une main détectée par frame et met à jour les états de gestes."""

    def __init__(
        self,
        pinch_confirm_frames: int = 3,
        pinch_min_hold: float = 0.05,
        pinch_cooldown: float = 0.3,
        pinch_threshold: float = 0.06,
    ):
        self._pinch = PinchGesture(
            threshold=pinch_threshold,
            confirm_frames=pinch_confirm_frames,
            min_hold_duration=pinch_min_hold,
            cooldown_duration=pinch_cooldown,
        )

    def process(self, hand_data: Optional[HandData], frame_width: int, frame_height: int) -> GestureSnapshot:
        if hand_data is None or not hand_data.is_valid:
            # Pas de main : on force la remontée à INACTIVE pour ne pas
            # rester bloqué dans un état si la main sort du champ pendant
            # un maintien.
            pinch_state = self._pinch.update({})
            return GestureSnapshot(
                hand_detected=False,
                gesture_name="NONE",
                state_name=pinch_state.name,
                confidence=0.0,
            )

        processed = process_landmarks(hand_data, frame_width, frame_height)
        signals = detect_raw_gestures(processed)
        pinch_state = self._pinch.update(processed.points_norm)

        gesture_name = "PINCH" if pinch_state != BinaryGestureState.INACTIVE else "NONE"

        return GestureSnapshot(
            hand_detected=True,
            gesture_name=gesture_name,
            state_name=pinch_state.name,
            confidence=processed.confidence,
            hand_openness=signals.hand_openness,
            index_tip_px=processed.points_px.get("index_tip"),
        )
