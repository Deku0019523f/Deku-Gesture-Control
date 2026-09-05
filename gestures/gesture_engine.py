"""
Moteur central de reconnaissance de gestes (spec section 8/9).

Phase 5 : le geste PINCH pilote clic gauche / double-clic / drag & drop,
et le geste deux-doigts pilote le clic droit. GestureEngine calcule
l'action à exécuter (GestureSnapshot.action) mais NE l'exécute PAS
lui-même : c'est CameraWorker (ui/main_window.py) qui appelle
MouseController en conséquence, pour garder ce module testable sans
piloter la souris réelle (spec section 25).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from gestures.gesture_detector import detect_raw_gestures
from gestures.gesture_state import BinaryGestureState
from gestures.gestures.click import ClickResolver
from gestures.gestures.drag import DragTracker
from gestures.gestures.pinch import PinchGesture
from gestures.gestures.two_fingers import TwoFingersGesture
from vision.hand_tracker import HandData
from vision.landmark_processor import process_landmarks


@dataclass
class GestureSnapshot:
    """État courant du moteur de gestes, pour affichage et pour piloter
    les actions souris (Phase 5)."""

    hand_detected: bool
    gesture_name: str
    state_name: str
    confidence: float
    hand_openness: float = 0.0
    index_tip_px: Optional[Tuple[int, int]] = None
    action: Optional[str] = None  # LEFT_CLICK | DOUBLE_CLICK | RIGHT_CLICK | DRAG_START | DRAG_MOVE | DRAG_END


class GestureEngine:
    def __init__(
        self,
        pinch_threshold: float = 0.06,
        pinch_confirm_frames: int = 3,
        pinch_min_hold: float = 0.05,
        pinch_cooldown: float = 0.3,
        drag_distance_threshold: float = 0.04,
        double_click_window: float = 0.35,
    ):
        self._pinch = PinchGesture(
            threshold=pinch_threshold,
            confirm_frames=pinch_confirm_frames,
            min_hold_duration=pinch_min_hold,
            cooldown_duration=pinch_cooldown,
        )
        self._two_fingers = TwoFingersGesture()
        self._drag = DragTracker(threshold=drag_distance_threshold)
        self._click_resolver = ClickResolver(double_click_window=double_click_window)

    def process(self, hand_data: Optional[HandData], frame_width: int, frame_height: int) -> GestureSnapshot:
        if hand_data is None or not hand_data.is_valid:
            pinch_state = self._pinch.update({})
            self._two_fingers.update({})

            action = None
            if self._drag.is_dragging:
                action = "DRAG_END"
                self._drag.reset()
            if action is None:
                action = self._click_resolver.tick()

            return GestureSnapshot(
                hand_detected=False,
                gesture_name="NONE",
                state_name=pinch_state.name,
                confidence=0.0,
                action=action,
            )

        processed = process_landmarks(hand_data, frame_width, frame_height)
        signals = detect_raw_gestures(processed)
        pinch_state = self._pinch.update(processed.points_norm)
        index_x, index_y, _ = processed.points_norm["index_tip"]

        # Le geste deux-doigts n'est évalué que lorsqu'aucun pinch n'est en
        # cours, pour éviter que les deux gestes ne se disputent une frame
        # ambiguë (spec section 10 : anti-faux-positifs).
        if pinch_state == BinaryGestureState.INACTIVE:
            two_fingers_state = self._two_fingers.update(processed.points_norm)
        else:
            two_fingers_state = self._two_fingers.update({})

        action: Optional[str] = None

        if pinch_state == BinaryGestureState.STARTED:
            self._drag.begin(index_x, index_y)
        elif pinch_state == BinaryGestureState.HOLDING:
            just_started_dragging = self._drag.update(index_x, index_y)
            if just_started_dragging:
                action = "DRAG_START"
            elif self._drag.is_dragging:
                action = "DRAG_MOVE"
        elif pinch_state == BinaryGestureState.RELEASED:
            if self._drag.is_dragging:
                action = "DRAG_END"
            else:
                action = self._click_resolver.on_click_candidate()
            self._drag.reset()

        if action is None and pinch_state == BinaryGestureState.INACTIVE and two_fingers_state == BinaryGestureState.RELEASED:
            action = "RIGHT_CLICK"

        if action is None:
            action = self._click_resolver.tick()

        if pinch_state != BinaryGestureState.INACTIVE:
            gesture_name, state_name = "PINCH", pinch_state.name
        elif two_fingers_state != BinaryGestureState.INACTIVE:
            gesture_name, state_name = "TWO_FINGERS", two_fingers_state.name
        else:
            gesture_name, state_name = "NONE", "INACTIVE"

        return GestureSnapshot(
            hand_detected=True,
            gesture_name=gesture_name,
            state_name=state_name,
            confidence=processed.confidence,
            hand_openness=signals.hand_openness,
            index_tip_px=processed.points_px.get("index_tip"),
            action=action,
        )
