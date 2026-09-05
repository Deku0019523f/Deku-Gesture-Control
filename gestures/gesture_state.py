"""
Machines à états pour les gestes (spec section 9), avec filtrage
anti-faux-positifs (spec section 10) : confirmation sur plusieurs frames,
durée minimale de maintien, cooldown.

DebouncedBinaryGesture est générique et réutilisable par n'importe quel
geste binaire (pinch aujourd'hui, d'autres gestes plus tard) sans dupliquer
cette logique (spec section 27 : ne pas réécrire le cœur du programme pour
ajouter un nouveau geste).
"""
from __future__ import annotations

import time
from enum import Enum, auto


class GestureState(Enum):
    """États génériques du pipeline de gestes (spec section 9)."""
    IDLE = auto()
    HAND_DETECTED = auto()
    GESTURE_DETECTED = auto()
    GESTURE_STARTED = auto()
    GESTURE_HOLDING = auto()
    GESTURE_RELEASED = auto()
    COOLDOWN = auto()


class BinaryGestureState(Enum):
    """États d'un geste binaire actif/inactif (ex. pinch)."""
    INACTIVE = auto()
    STARTED = auto()
    HOLDING = auto()
    RELEASED = auto()
    COOLDOWN = auto()


class DebouncedBinaryGesture:
    """Filtre temporel générique pour un geste binaire.

    Transforme un signal brut (True/False, calculé à chaque frame) en
    transitions d'état fiables, pour éviter qu'un geste détecté sur une
    seule frame ne déclenche immédiatement une action (spec section 10).
    """

    def __init__(
        self,
        confirm_frames: int = 3,
        min_hold_duration: float = 0.05,
        cooldown_duration: float = 0.3,
    ):
        self.confirm_frames = confirm_frames
        self.min_hold_duration = min_hold_duration
        self.cooldown_duration = cooldown_duration

        self.state = BinaryGestureState.INACTIVE
        self._positive_streak = 0
        self._negative_streak = 0
        self._state_entered_at = time.perf_counter()

    def update(self, raw_signal: bool) -> BinaryGestureState:
        """À appeler une fois par frame avec le signal brut (ex. is_pinch())."""
        now = time.perf_counter()

        if raw_signal:
            self._positive_streak += 1
            self._negative_streak = 0
        else:
            self._negative_streak += 1
            self._positive_streak = 0

        if self.state == BinaryGestureState.INACTIVE:
            if self._positive_streak >= self.confirm_frames:
                self._transition(BinaryGestureState.STARTED, now)

        elif self.state == BinaryGestureState.STARTED:
            if now - self._state_entered_at >= self.min_hold_duration:
                self._transition(BinaryGestureState.HOLDING, now)
            elif self._negative_streak >= self.confirm_frames:
                self._transition(BinaryGestureState.INACTIVE, now)

        elif self.state == BinaryGestureState.HOLDING:
            if self._negative_streak >= self.confirm_frames:
                self._transition(BinaryGestureState.RELEASED, now)

        elif self.state == BinaryGestureState.RELEASED:
            # État transitoire : consommé une frame puis passage en cooldown.
            self._transition(BinaryGestureState.COOLDOWN, now)

        elif self.state == BinaryGestureState.COOLDOWN:
            if now - self._state_entered_at >= self.cooldown_duration:
                self._transition(BinaryGestureState.INACTIVE, now)

        return self.state

    def _transition(self, new_state: BinaryGestureState, now: float) -> None:
        self.state = new_state
        self._state_entered_at = now
