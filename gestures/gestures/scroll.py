"""
Geste de scroll (spec section 8 : "Détecter un mouvement vertical
contrôlé de la main").

Réutilise la forme "deux doigts" (index + majeur tendus) déjà détectée
pour le clic droit (Phase 5) : un maintien bref et immobile reste un clic
droit ; un déplacement vertical au-delà d'un seuil bascule en scroll
continu tant que le geste est maintenu (comme un trackpad).
"""
from __future__ import annotations

from typing import Optional, Tuple

SCROLL_ENGAGE_THRESHOLD = 0.03  # distance verticale normalisée avant d'engager le scroll
SCROLL_SENSITIVITY = 800  # conversion delta normalisé -> "ticks" de molette


class ScrollTracker:
    def __init__(self, engage_threshold: float = SCROLL_ENGAGE_THRESHOLD, sensitivity: float = SCROLL_SENSITIVITY):
        self.engage_threshold = engage_threshold
        self.sensitivity = sensitivity
        self._start_y: Optional[float] = None
        self._last_y: Optional[float] = None
        self._scrolling: bool = False

    def begin(self, y: float) -> None:
        """À appeler au moment où le geste deux-doigts entre en HOLDING."""
        self._start_y = y
        self._last_y = y
        self._scrolling = False

    def update(self, y: float) -> int:
        """À appeler à chaque frame pendant HOLDING. Retourne le delta de
        scroll à appliquer (0 si le scroll n'est pas encore engagé)."""
        if self._start_y is None:
            self.begin(y)
            return 0

        if not self._scrolling and abs(y - self._start_y) >= self.engage_threshold:
            self._scrolling = True

        if not self._scrolling:
            return 0

        dy = self._last_y - y  # main vers le haut (y diminue) -> scroll vers le haut (positif)
        self._last_y = y
        return int(dy * self.sensitivity)

    @property
    def is_scrolling(self) -> bool:
        return self._scrolling

    def reset(self) -> None:
        self._start_y = None
        self._last_y = None
        self._scrolling = False
