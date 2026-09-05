"""
Landmark Processor : convertit les landmarks normalisés d'un HandData en
coordonnées pixel et permet un accès par nom aux points de la main
(spec section 4/6, pipeline Hand Landmarks -> Landmark Processor).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from vision.hand_tracker import HandData

LANDMARK_NAMES = [
    "wrist",
    "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip",
    "index_mcp", "index_pip", "index_dip", "index_tip",
    "middle_mcp", "middle_pip", "middle_dip", "middle_tip",
    "ring_mcp", "ring_pip", "ring_dip", "ring_tip",
    "pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip",
]


@dataclass
class ProcessedHand:
    """Main avec landmarks indexables par nom, en pixels et en normalisé."""

    points_px: Dict[str, Tuple[int, int]]
    points_norm: Dict[str, Tuple[float, float, float]]
    confidence: float
    handedness: str


def process_landmarks(hand_data: HandData, frame_width: int, frame_height: int) -> ProcessedHand:
    """Transforme un HandData brut en ProcessedHand utilisable par hand_geometry."""
    points_px: Dict[str, Tuple[int, int]] = {}
    points_norm: Dict[str, Tuple[float, float, float]] = {}

    for name, (x, y, z) in zip(LANDMARK_NAMES, hand_data.landmarks):
        points_norm[name] = (x, y, z)
        points_px[name] = (int(x * frame_width), int(y * frame_height))

    return ProcessedHand(
        points_px=points_px,
        points_norm=points_norm,
        confidence=hand_data.confidence,
        handedness=hand_data.handedness,
    )
