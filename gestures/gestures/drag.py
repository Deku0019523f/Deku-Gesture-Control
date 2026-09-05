"""
Geste de glisser-déposer : PINCH HOLD -> déplacement -> RELEASE
(spec section 8/14).

DragTracker observe la position de l'index pendant qu'un pinch est
maintenu (PINCH_HOLDING) et décide, une fois un seuil de déplacement
franchi, que le pinch devient un drag plutôt qu'un simple clic maintenu
immobile.
"""
from __future__ import annotations

from typing import Optional, Tuple

DRAG_DISTANCE_THRESHOLD = 0.04  # distance normalisée à partir de laquelle un pinch maintenu devient un drag


class DragTracker:
    def __init__(self, threshold: float = DRAG_DISTANCE_THRESHOLD):
        self.threshold = threshold
        self._start_pos: Optional[Tuple[float, float]] = None
        self._dragging: bool = False

    def begin(self, x: float, y: float) -> None:
        """À appeler au moment où le pinch entre en STARTED/HOLDING."""
        self._start_pos = (x, y)
        self._dragging = False

    def update(self, x: float, y: float) -> bool:
        """À appeler à chaque frame pendant HOLDING.

        Retourne True la frame où le drag vient tout juste de s'engager
        (transition clic-maintenu -> drag), False sinon.
        """
        if self._start_pos is None:
            self._start_pos = (x, y)
            return False

        if not self._dragging:
            dx = x - self._start_pos[0]
            dy = y - self._start_pos[1]
            if (dx * dx + dy * dy) ** 0.5 >= self.threshold:
                self._dragging = True
                return True
        return False

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    def reset(self) -> None:
        self._start_pos = None
        self._dragging = False
