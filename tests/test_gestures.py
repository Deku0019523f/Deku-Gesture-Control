"""
Tests unitaires pour le pipeline de gestes (spec section 25) : clic,
double-clic, drag, scroll, swipe.

GestureEngine ne pilote jamais la souris/le clavier lui-même (spec
section 25) : ces tests vérifient uniquement les GestureSnapshot.action
produits. Le dispatch réel vers MouseController/KeyboardController
(CameraWorker._dispatch_action) est testé séparément avec des mocks, pour
garantir qu'aucun test ne déplace la souris ou n'envoie de vraies touches.
"""
import time
from unittest.mock import MagicMock

import pytest

from camera.camera_manager import CameraManager
from gestures.gesture_engine import GestureEngine
from ui.camera_view import CameraWorker
from vision.hand_tracker import HandData

FRAME_DT = 1 / 30
W, H = 640, 480


def make_landmarks(index=(0.5, 0.5), thumb=(0.9, 0.9), wrist=(0.5, 0.7),
                    middle_extended=False, ring_extended=False, pinky_extended=False):
    pts = [(0.5, 0.5, 0.0)] * 21
    pts[0] = (wrist[0], wrist[1], 0.0)
    pts[5] = (0.5, 0.6, 0.0)
    pts[6] = (0.5, 0.55, 0.0)
    pts[8] = (index[0], index[1], 0.0)
    pts[1] = (0.9, 0.95, 0.0)
    pts[2] = (0.9, 0.92, 0.0)
    pts[4] = (thumb[0], thumb[1], 0.0)

    def finger(base_idx, pip_idx, tip_idx, x, extended):
        if extended:
            pts[base_idx], pts[pip_idx], pts[tip_idx] = (x, 0.6, 0.0), (x, 0.55, 0.0), (x, 0.5, 0.0)
        else:
            pts[base_idx], pts[pip_idx], pts[tip_idx] = (x, 0.6, 0.0), (x, 0.62, 0.0), (x, 0.6, 0.0)

    finger(9, 10, 12, 0.55, middle_extended)
    finger(13, 14, 16, 0.60, ring_extended)
    finger(17, 18, 20, 0.65, pinky_extended)
    return pts


def hand(**kwargs) -> HandData:
    return HandData(landmarks=make_landmarks(**kwargs), confidence=0.95, handedness="Right", bounding_box=(0, 0, 1, 1))


def step(engine: GestureEngine, **kwargs):
    """Simule l'écoulement d'une frame réelle (~30fps) avant de traiter la main."""
    time.sleep(FRAME_DT)
    return engine.process(hand(**kwargs), W, H)


class TestLeftClick:
    def test_brief_pinch_eventually_fires_left_click(self):
        engine = GestureEngine(pinch_confirm_frames=3, pinch_min_hold=0.0, pinch_cooldown=0.05)
        actions = []
        for _ in range(3):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.5, 0.5)).action)
        for _ in range(6):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.9, 0.9)).action)
        time.sleep(0.4)  # laisse expirer la fenêtre de double-clic
        actions.append(engine.process(None, W, H).action)
        assert actions.count("LEFT_CLICK") == 1
        assert "DOUBLE_CLICK" not in actions

    def test_single_frame_pinch_never_triggers_click(self):
        """Anti-faux-positif (spec section 10) : un pinch détecté sur une
        seule frame ne doit jamais déclencher de clic."""
        engine = GestureEngine(pinch_confirm_frames=3, pinch_min_hold=0.0, pinch_cooldown=0.05)
        actions = [step(engine, index=(0.5, 0.5), thumb=(0.5, 0.5)).action]  # une seule frame de pinch
        for _ in range(6):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.9, 0.9)).action)
        time.sleep(0.4)
        actions.append(engine.process(None, W, H).action)
        assert "LEFT_CLICK" not in actions


class TestDoubleClick:
    def test_two_rapid_pinches_fire_double_click_not_two_singles(self):
        engine = GestureEngine(pinch_confirm_frames=3, pinch_min_hold=0.0, pinch_cooldown=0.05)

        def pinch_cycle():
            res = []
            for _ in range(3):
                res.append(step(engine, index=(0.5, 0.5), thumb=(0.5, 0.5)).action)
            for _ in range(5):
                res.append(step(engine, index=(0.5, 0.5), thumb=(0.9, 0.9)).action)
            return res

        actions = pinch_cycle() + pinch_cycle()
        assert "DOUBLE_CLICK" in actions
        assert actions.count("LEFT_CLICK") == 0


class TestDragAndDrop:
    def test_pinch_hold_and_move_produces_drag_not_click(self):
        engine = GestureEngine(pinch_confirm_frames=3, pinch_min_hold=0.0, pinch_cooldown=0.05, drag_distance_threshold=0.04)
        actions = []
        for _ in range(3):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.5, 0.5)).action)
        for x in (0.52, 0.56, 0.62, 0.70):
            actions.append(step(engine, index=(x, 0.5), thumb=(x, 0.5)).action)
        for _ in range(5):
            actions.append(step(engine, index=(0.70, 0.5), thumb=(0.9, 0.9)).action)
        time.sleep(0.4)
        actions.append(engine.process(None, W, H).action)

        assert "DRAG_START" in actions
        assert "DRAG_END" in actions
        assert "LEFT_CLICK" not in actions

    def test_small_movement_stays_a_click_not_a_drag(self):
        """Un pinch maintenu avec un tremblement minime (sous le seuil)
        doit rester un clic, pas un drag."""
        engine = GestureEngine(pinch_confirm_frames=3, pinch_min_hold=0.0, pinch_cooldown=0.05, drag_distance_threshold=0.04)
        actions = []
        for _ in range(3):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.5, 0.5)).action)
        for x in (0.505, 0.502, 0.507):  # micro-mouvements, sous le seuil
            actions.append(step(engine, index=(x, 0.5), thumb=(x, 0.5)).action)
        for _ in range(5):
            actions.append(step(engine, index=(0.507, 0.5), thumb=(0.9, 0.9)).action)
        time.sleep(0.4)
        actions.append(engine.process(None, W, H).action)

        assert "DRAG_START" not in actions
        assert actions.count("LEFT_CLICK") == 1


class TestRightClick:
    def test_two_fingers_tap_fires_right_click(self):
        engine = GestureEngine()
        actions = []
        for _ in range(4):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.9, 0.9), middle_extended=True).action)
        for _ in range(4):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.9, 0.9), middle_extended=False).action)
        assert "RIGHT_CLICK" in actions

    def test_pinch_never_triggers_right_click(self):
        engine = GestureEngine(pinch_confirm_frames=3, pinch_min_hold=0.0)
        actions = []
        for _ in range(6):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.5, 0.5)).action)
        assert "RIGHT_CLICK" not in actions


class TestScroll:
    def test_two_fingers_vertical_move_produces_scroll(self):
        engine = GestureEngine()
        actions = []
        for _ in range(4):
            actions.append(step(engine, index=(0.5, 0.5), thumb=(0.9, 0.9), middle_extended=True).action)
        results = []
        for y in (0.45, 0.38, 0.30, 0.22, 0.15):
            snap = step(engine, index=(0.5, y), thumb=(0.9, 0.9), middle_extended=True)
            results.append((snap.action, snap.action_value))
        for _ in range(4):
            actions.append(step(engine, index=(0.5, 0.15), thumb=(0.9, 0.9), middle_extended=False).action)

        scroll_events = [r for r in results if r[0] == "SCROLL"]
        assert len(scroll_events) > 0
        assert all(v > 0 for _, v in scroll_events)  # main vers le haut -> delta positif
        assert "RIGHT_CLICK" not in actions  # un scroll ne doit pas finir en clic droit


class TestSwipe:
    def test_open_hand_fast_move_triggers_swipe_right(self):
        engine = GestureEngine()
        actions = []
        for _ in range(3):
            actions.append(step(
                engine, index=(0.3, 0.5), wrist=(0.3, 0.7),
                middle_extended=True, ring_extended=True, pinky_extended=True,
            ).action)
        for x in (0.35, 0.5, 0.7, 0.9):
            actions.append(step(
                engine, index=(x, 0.5), wrist=(x, 0.7),
                middle_extended=True, ring_extended=True, pinky_extended=True,
            ).action)
        assert "SWIPE_RIGHT" in actions

    def test_pointing_hand_never_triggers_swipe(self):
        """Le pointage normal (index seul tendu, déplacé rapidement) ne
        doit jamais être confondu avec un swipe (spec : main ouverte requise)."""
        engine = GestureEngine()
        actions = []
        for x in (0.2, 0.4, 0.6, 0.8, 0.95):
            actions.append(step(engine, index=(x, 0.5), wrist=(x, 0.7)).action)  # rien d'étendu sauf l'index
        assert not any(a and a.startswith("SWIPE") for a in actions)


class TestPause:
    def test_open_hand_held_still_triggers_pause_once(self):
        engine = GestureEngine()
        actions = []
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < 1.3:
            snap = engine.process(
                hand(index=(0.5, 0.5), wrist=(0.5, 0.7), middle_extended=True, ring_extended=True, pinky_extended=True),
                W, H,
            )
            actions.append(snap.action)
            time.sleep(FRAME_DT)
        assert actions.count("PAUSE_TOGGLE") == 1

    def test_brief_open_hand_does_not_trigger_pause(self):
        engine = GestureEngine()
        actions = []
        for _ in range(5):  # bien moins d'1 seconde
            actions.append(step(
                engine, index=(0.5, 0.5), wrist=(0.5, 0.7),
                middle_extended=True, ring_extended=True, pinky_extended=True,
            ).action)
        assert "PAUSE_TOGGLE" not in actions


class TestActionDispatch:
    """Vérifie que CameraWorker._dispatch_action appelle les bonnes méthodes
    du contrôleur souris/clavier — toujours avec des mocks (spec section 25 :
    ces tests ne doivent jamais déplacer la souris réelle)."""

    def _make_worker(self, mapping=None):
        camera_manager = MagicMock(spec=CameraManager)
        return CameraWorker(camera_manager, settings={}, gestures_mapping=mapping or {})

    def _snapshot(self, action, action_value=None):
        from gestures.gesture_engine import GestureSnapshot
        return GestureSnapshot(hand_detected=True, gesture_name="X", state_name="X", confidence=1.0, action=action, action_value=action_value)

    def test_left_click_dispatched(self):
        worker = self._make_worker()
        mouse, keyboard = MagicMock(), MagicMock()
        worker._dispatch_action(self._snapshot("LEFT_CLICK"), mouse, keyboard)
        mouse.left_click.assert_called_once()

    def test_double_click_dispatched(self):
        worker = self._make_worker()
        mouse, keyboard = MagicMock(), MagicMock()
        worker._dispatch_action(self._snapshot("DOUBLE_CLICK"), mouse, keyboard)
        mouse.double_click.assert_called_once()

    def test_right_click_respects_disabled_mapping(self):
        worker = self._make_worker(mapping={"two_fingers": "none"})
        mouse, keyboard = MagicMock(), MagicMock()
        worker._dispatch_action(self._snapshot("RIGHT_CLICK"), mouse, keyboard)
        mouse.right_click.assert_not_called()

    def test_drag_start_and_end_dispatched(self):
        worker = self._make_worker()
        mouse, keyboard = MagicMock(), MagicMock()
        worker._dispatch_action(self._snapshot("DRAG_START"), mouse, keyboard)
        worker._dispatch_action(self._snapshot("DRAG_END"), mouse, keyboard)
        mouse.drag_start.assert_called_once()
        mouse.drag_end.assert_called_once()

    def test_scroll_forwards_amount(self):
        worker = self._make_worker()
        mouse, keyboard = MagicMock(), MagicMock()
        worker._dispatch_action(self._snapshot("SCROLL", action_value=42), mouse, keyboard)
        mouse.scroll.assert_called_once_with(42)

    def test_swipe_triggers_mapped_keyboard_action(self):
        worker = self._make_worker(mapping={"swipe_left": "previous"})
        mouse, keyboard = MagicMock(), MagicMock()
        keyboard.trigger_named.return_value = True
        worker._dispatch_action(self._snapshot("SWIPE_LEFT"), mouse, keyboard)
        keyboard.trigger_named.assert_called_once_with("previous")

    def test_swipe_disabled_in_mapping_still_calls_trigger_with_none(self):
        worker = self._make_worker(mapping={"swipe_up": "none"})
        mouse, keyboard = MagicMock(), MagicMock()
        keyboard.trigger_named.return_value = False
        worker._dispatch_action(self._snapshot("SWIPE_UP"), mouse, keyboard)
        keyboard.trigger_named.assert_called_once_with("none")
