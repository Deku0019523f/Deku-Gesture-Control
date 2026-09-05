"""
Détection des gestes bruts, frame par frame, à partir de la géométrie de
la main (spec section 8). Sert notamment à afficher l'état des doigts
pendant les tests de la Phase 3, indépendamment du filtrage temporel des
gestes concrets (pinch, etc.) fait dans gestures/gestures/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from vision import hand_geometry as geo
from vision.landmark_processor import ProcessedHand


@dataclass
class RawGestureSignals:
    """Signaux bruts calculés pour une frame donnée (avant filtrage temporel)."""

    is_pinch: bool
    hand_openness: float
    fingers_extended: Dict[str, bool] = field(default_factory=dict)


def detect_raw_gestures(hand: ProcessedHand, pinch_threshold: float = geo.DEFAULT_PINCH_THRESHOLD) -> RawGestureSignals:
    points = hand.points_norm
    fingers_extended = {finger: geo.is_finger_extended(points, finger) for finger in geo.FINGER_JOINTS}
    return RawGestureSignals(
        is_pinch=geo.is_pinch(points, threshold=pinch_threshold),
        hand_openness=geo.hand_openness(points),
        fingers_extended=fingers_extended,
    )
