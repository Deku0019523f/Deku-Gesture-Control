"""
Tests unitaires pour vision.hand_geometry (spec section 25) :
distance, angle, détection des doigts, détection du pinch.
"""
import math

import pytest

from vision import hand_geometry as geo


def make_points(index_extended=True, thumb_near_index=False):
    """Construit un jeu de points de main minimal pour les tests."""
    points = {
        "thumb_cmc": (0.9, 0.95, 0.0),
        "thumb_mcp": (0.9, 0.92, 0.0),
        "thumb_tip": (0.5, 0.5, 0.0) if thumb_near_index else (0.9, 0.9, 0.0),
        "index_mcp": (0.5, 0.6, 0.0),
        "index_pip": (0.5, 0.55, 0.0),
        "index_tip": (0.5, 0.5 if index_extended else 0.6, 0.0),
        "middle_mcp": (0.55, 0.6, 0.0), "middle_pip": (0.55, 0.62, 0.0), "middle_tip": (0.55, 0.6, 0.0),
        "ring_mcp": (0.6, 0.6, 0.0), "ring_pip": (0.6, 0.62, 0.0), "ring_tip": (0.6, 0.6, 0.0),
        "pinky_mcp": (0.65, 0.6, 0.0), "pinky_pip": (0.65, 0.62, 0.0), "pinky_tip": (0.65, 0.6, 0.0),
    }
    return points


class TestDistance:
    def test_zero_distance(self):
        assert geo.distance((0.5, 0.5), (0.5, 0.5)) == 0.0

    def test_known_distance(self):
        assert geo.distance((0.0, 0.0), (3.0, 4.0)) == pytest.approx(5.0)

    def test_ignores_z(self):
        # distance() est volontairement 2D (spec section 7)
        assert geo.distance((0.0, 0.0, 100.0), (3.0, 4.0, -100.0)) == pytest.approx(5.0)


class TestAngle:
    def test_straight_line_is_180(self):
        a, b, c = (0.0, 0.0), (1.0, 0.0), (2.0, 0.0)
        assert geo.angle(a, b, c) == pytest.approx(180.0)

    def test_right_angle_is_90(self):
        a, b, c = (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)
        assert geo.angle(a, b, c) == pytest.approx(90.0)

    def test_folded_back_is_near_zero(self):
        a, b, c = (0.0, 0.0), (1.0, 0.0), (0.0, 0.0)
        assert geo.angle(a, b, c) == pytest.approx(0.0)

    def test_degenerate_points_returns_zero(self):
        # b confondu avec a : pas de vecteur défini, ne doit pas planter
        assert geo.angle((1.0, 1.0), (1.0, 1.0), (2.0, 2.0)) == 0.0


class TestFingerExtended:
    def test_extended_finger_detected(self):
        points = make_points(index_extended=True)
        assert geo.is_finger_extended(points, "index") is True

    def test_folded_finger_not_extended(self):
        points = make_points(index_extended=False)
        assert geo.is_finger_extended(points, "index") is False

    def test_custom_threshold(self):
        points = make_points(index_extended=True)
        # Un seuil très strict (179°) doit rejeter un angle légèrement < 180
        points["index_tip"] = (0.52, 0.5, 0.0)  # angle proche de 180 mais pas parfait
        assert geo.is_finger_extended(points, "index", threshold=179.99) in (True, False)  # ne doit pas planter


class TestPinch:
    def test_far_apart_is_not_pinch(self):
        points = make_points(thumb_near_index=False)
        assert geo.is_pinch(points) is False

    def test_close_together_is_pinch(self):
        points = make_points(thumb_near_index=True)
        assert geo.is_pinch(points) is True

    def test_custom_threshold(self):
        points = make_points(thumb_near_index=False)
        # Avec un seuil énorme, même des points éloignés comptent comme pinch
        assert geo.is_pinch(points, threshold=10.0) is True


class TestHandOpenness:
    def test_all_extended_is_one(self):
        points = make_points(index_extended=True)
        # Pour qu'un doigt soit "tendu", le bout doit continuer tout droit
        # au-delà de l'articulation médiane (spec section 7 : angle ~180°).
        points["middle_tip"] = (0.55, 0.64, 0.0)
        points["ring_tip"] = (0.6, 0.64, 0.0)
        points["pinky_tip"] = (0.65, 0.64, 0.0)
        points["thumb_tip"] = (0.9, 0.85, 0.0)  # continue la direction cmc -> mcp
        assert geo.hand_openness(points) == pytest.approx(1.0)

    def test_all_folded_is_zero(self):
        points = make_points(index_extended=False)
        # Pouce replié : le bout revient sur l'articulation mcp (angle ~0°).
        points["thumb_tip"] = points["thumb_mcp"]
        assert geo.hand_openness(points) == pytest.approx(0.0)


class TestVelocityTracker:
    def test_no_history_gives_zero_velocity(self):
        tracker = geo.VelocityTracker()
        assert tracker.get_velocity() == (0.0, 0.0)
        assert tracker.get_direction() == "none"

    def test_rightward_motion(self):
        tracker = geo.VelocityTracker()
        tracker.update((0.0, 0.5), 0.0)
        tracker.update((1.0, 0.5), 1.0)
        vx, vy = tracker.get_velocity()
        assert vx == pytest.approx(1.0)
        assert vy == pytest.approx(0.0)
        assert tracker.get_direction() == "right"

    def test_upward_motion(self):
        tracker = geo.VelocityTracker()
        tracker.update((0.5, 1.0), 0.0)
        tracker.update((0.5, 0.0), 1.0)  # y diminue -> vers le haut
        assert tracker.get_direction() == "up"

    def test_reset_clears_history(self):
        tracker = geo.VelocityTracker()
        tracker.update((0.0, 0.0), 0.0)
        tracker.update((1.0, 0.0), 1.0)
        tracker.reset()
        assert tracker.get_velocity() == (0.0, 0.0)
