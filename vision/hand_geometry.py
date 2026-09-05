"""
Analyse géométrique de la main (spec section 7) : fonctions réutilisables
et testables, indépendantes de MediaPipe et de Qt.

Les points reçus par ces fonctions sont des dict {nom: (x, y, z)} produits
par vision.landmark_processor.process_landmarks (coordonnées normalisées
0..1), ou tout mapping équivalent nom -> point.
"""
from __future__ import annotations

import math
from collections import deque
from typing import Deque, Dict, Sequence, Tuple

Point = Sequence[float]  # (x, y) ou (x, y, z) ; seuls x et y sont utilisés en 2D

# Articulations utilisées pour juger si un doigt est tendu : (base, milieu, bout)
# Le pouce n'a pas de "pip" classique, on utilise donc (cmc, mcp, tip).
FINGER_JOINTS = {
    "thumb": ("thumb_cmc", "thumb_mcp", "thumb_tip"),
    "index": ("index_mcp", "index_pip", "index_tip"),
    "middle": ("middle_mcp", "middle_pip", "middle_tip"),
    "ring": ("ring_mcp", "ring_pip", "ring_tip"),
    "pinky": ("pinky_mcp", "pinky_pip", "pinky_tip"),
}

EXTENDED_ANGLE_THRESHOLD = 160.0  # degrés : au-delà, le doigt est considéré tendu
DEFAULT_PINCH_THRESHOLD = 0.06  # distance normalisée pouce-index


def distance(p1: Point, p2: Point) -> float:
    """Distance euclidienne 2D entre deux points (x, y[, z])."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def angle(a: Point, b: Point, c: Point) -> float:
    """Angle (en degrés) au sommet b, formé par les points a-b-c."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.hypot(*ba)
    mag_bc = math.hypot(*bc)
    if mag_ba == 0 or mag_bc == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def is_finger_extended(points: Dict[str, Point], finger: str, threshold: float = EXTENDED_ANGLE_THRESHOLD) -> bool:
    """Un doigt est considéré tendu si l'angle à son articulation médiane est proche de 180°."""
    base, mid, tip = FINGER_JOINTS[finger]
    return angle(points[base], points[mid], points[tip]) >= threshold


def is_pinch(points: Dict[str, Point], threshold: float = DEFAULT_PINCH_THRESHOLD) -> bool:
    """Pinch = pouce et index suffisamment proches (distance normalisée)."""
    return distance(points["thumb_tip"], points["index_tip"]) < threshold


def hand_openness(points: Dict[str, Point]) -> float:
    """Proportion de doigts tendus (0.0 = poing fermé, 1.0 = main grande ouverte)."""
    extended = sum(1 for f in FINGER_JOINTS if is_finger_extended(points, f))
    return extended / len(FINGER_JOINTS)


class VelocityTracker:
    """Calcule la vitesse et la direction du mouvement d'un point dans le temps."""

    def __init__(self, history_size: int = 5):
        self._history: Deque[Tuple[float, float, float]] = deque(maxlen=history_size)

    def update(self, point: Point, timestamp: float) -> None:
        self._history.append((point[0], point[1], timestamp))

    def get_velocity(self) -> Tuple[float, float]:
        """Vitesse (dx/dt, dy/dt) entre le premier et le dernier point de l'historique."""
        if len(self._history) < 2:
            return (0.0, 0.0)
        x0, y0, t0 = self._history[0]
        x1, y1, t1 = self._history[-1]
        dt = t1 - t0
        if dt <= 0:
            return (0.0, 0.0)
        return ((x1 - x0) / dt, (y1 - y0) / dt)

    def get_direction(self, min_speed: float = 0.05) -> str:
        """Direction dominante du mouvement : left/right/up/down/none."""
        vx, vy = self.get_velocity()
        if abs(vx) < min_speed and abs(vy) < min_speed:
            return "none"
        if abs(vx) > abs(vy):
            return "right" if vx > 0 else "left"
        return "down" if vy > 0 else "up"

    def reset(self) -> None:
        self._history.clear()
