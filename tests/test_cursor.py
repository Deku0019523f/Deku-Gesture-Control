"""
Tests unitaires pour le module cursor (spec section 25) : mapping de
coordonnées, limites d'écran, lissage, calibration.

Ces tests ne déplacent jamais réellement la souris : MouseController est
systématiquement remplacé par un mock (spec section 25).
"""
from unittest.mock import MagicMock

import pytest

from cursor.calibration import Calibration
from cursor.cursor_controller import CursorController
from cursor.smoothing import ExponentialSmoother, MovingAverageSmoother, create_smoother


class TestCalibration:
    def test_center_of_active_zone_is_half(self):
        calib = Calibration(active_left=0.2, active_top=0.2, active_right=0.8, active_bottom=0.8)
        x_rel, y_rel = calib.to_relative(0.5, 0.5)
        assert x_rel == pytest.approx(0.5)
        assert y_rel == pytest.approx(0.5)

    def test_left_edge_of_active_zone_is_zero(self):
        calib = Calibration(active_left=0.2, active_top=0.2, active_right=0.8, active_bottom=0.8)
        x_rel, _ = calib.to_relative(0.2, 0.5)
        assert x_rel == pytest.approx(0.0)

    def test_right_edge_of_active_zone_is_one(self):
        calib = Calibration(active_left=0.2, active_top=0.2, active_right=0.8, active_bottom=0.8)
        x_rel, _ = calib.to_relative(0.8, 0.5)
        assert x_rel == pytest.approx(1.0)

    def test_point_outside_active_zone_is_not_clamped_here(self):
        # to_relative() ne clampe pas : c'est CursorController qui le fait
        # après application de la sensibilité.
        calib = Calibration(active_left=0.2, active_top=0.2, active_right=0.8, active_bottom=0.8)
        x_rel, _ = calib.to_relative(0.0, 0.5)
        assert x_rel < 0.0


class TestSmoothing:
    def test_exponential_first_call_returns_input(self):
        smoother = ExponentialSmoother(smoothing_strength=0.5)
        x, y = smoother.smooth(100.0, 200.0)
        assert (x, y) == (100.0, 200.0)

    def test_exponential_dampens_sudden_jump(self):
        smoother = ExponentialSmoother(smoothing_strength=0.9)  # très lissé
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(1000.0, 1000.0)
        assert 0.0 < x < 1000.0  # ne saute pas instantanément à la cible

    def test_exponential_zero_strength_follows_target_immediately(self):
        smoother = ExponentialSmoother(smoothing_strength=0.0)
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(500.0, 500.0)
        assert (x, y) == pytest.approx((500.0, 500.0))

    def test_moving_average_smooths_over_window(self):
        smoother = MovingAverageSmoother(window_size=4)
        smoother.smooth(0.0, 0.0)
        smoother.smooth(0.0, 0.0)
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(100.0, 100.0)
        assert x == pytest.approx(25.0)  # (0+0+0+100)/4

    def test_reset_clears_state(self):
        smoother = ExponentialSmoother(smoothing_strength=0.9)
        smoother.smooth(0.0, 0.0)
        smoother.reset()
        x, y = smoother.smooth(500.0, 500.0)
        assert (x, y) == (500.0, 500.0)  # comme un premier appel

    def test_factory_returns_configured_smoother(self):
        assert isinstance(create_smoother(mode="moving_average"), MovingAverageSmoother)
        assert isinstance(create_smoother(mode="exponential"), ExponentialSmoother)


class TestCursorController:
    def _make_mock_mouse(self, screen_size=(1920, 1080)):
        mouse = MagicMock()
        mouse.get_screen_size.return_value = screen_size
        return mouse

    def test_center_maps_to_screen_center(self):
        mouse = self._make_mock_mouse((1920, 1080))
        controller = CursorController(mouse_controller=mouse, smoothing_strength=0.0, dead_zone=0.0)
        controller.update(0.5, 0.5)
        args, _ = mouse.move.call_args
        assert args[0] == pytest.approx(960, abs=1)
        assert args[1] == pytest.approx(540, abs=1)

    def test_output_never_exceeds_screen_boundaries(self):
        mouse = self._make_mock_mouse((1920, 1080))
        controller = CursorController(mouse_controller=mouse, smoothing_strength=0.0, dead_zone=0.0)
        # Position bien au-delà de la zone active -> doit être clampée à l'écran
        controller.update(-5.0, -5.0)
        x, y = mouse.move.call_args[0]
        assert 0 <= x <= 1920
        assert 0 <= y <= 1080

        controller.update(50.0, 50.0)
        x, y = mouse.move.call_args[0]
        assert 0 <= x <= 1920
        assert 0 <= y <= 1080

    def test_dead_zone_suppresses_micro_movements(self):
        mouse = self._make_mock_mouse((1920, 1080))
        controller = CursorController(mouse_controller=mouse, smoothing_strength=0.0, dead_zone=0.5)
        controller.update(0.5, 0.5)
        mouse.move.reset_mock()
        controller.update(0.501, 0.501)  # micro-mouvement, sous le seuil de la zone morte
        mouse.move.assert_not_called()

    def test_sensitivity_amplifies_movement_from_center(self):
        mouse_low = self._make_mock_mouse((1920, 1080))
        mouse_high = self._make_mock_mouse((1920, 1080))
        low = CursorController(mouse_controller=mouse_low, sensitivity=1.0, smoothing_strength=0.0, dead_zone=0.0)
        high = CursorController(mouse_controller=mouse_high, sensitivity=2.0, smoothing_strength=0.0, dead_zone=0.0)

        low.update(0.7, 0.5)
        high.update(0.7, 0.5)

        x_low, _ = mouse_low.move.call_args[0]
        x_high, _ = mouse_high.move.call_args[0]
        # Avec une sensibilité plus élevée, le même déplacement de la main
        # doit produire un déplacement plus grand à l'écran par rapport au centre.
        assert abs(x_high - 960) > abs(x_low - 960)

    def test_reset_clears_internal_state(self):
        mouse = self._make_mock_mouse((1920, 1080))
        controller = CursorController(mouse_controller=mouse, smoothing_strength=0.9, dead_zone=0.0)
        controller.update(0.5, 0.5)
        controller.reset()
        mouse.move.reset_mock()
        controller.update(0.9, 0.9)
        # Après reset, le lissage repart de zéro : le mouvement ne doit pas
        # être ralenti par l'ancienne position mémorisée.
        assert mouse.move.called
