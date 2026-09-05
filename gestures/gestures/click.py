"""
Clic gauche et double-clic, dérivés d'un pinch bref sans déplacement
(spec section 8) : "Double clic : Deux pinch rapides."

ClickResolver reçoit chaque relâchement de pinch qui n'a PAS été
requalifié en drag, et distingue un simple clic d'un double-clic en
différant l'action le temps de voir si un second pinch arrive assez vite.
"""
from __future__ import annotations

import time
from typing import Optional

DOUBLE_CLICK_WINDOW = 0.35  # secondes max entre deux pinch pour former un double-clic


class ClickResolver:
    def __init__(self, double_click_window: float = DOUBLE_CLICK_WINDOW):
        self.double_click_window = double_click_window
        self._pending_since: Optional[float] = None

    def on_click_candidate(self) -> Optional[str]:
        """À appeler quand un pinch bref (non-drag) vient d'être relâché.

        Retourne "DOUBLE_CLICK" immédiatement si un clic était déjà en
        attente dans la fenêtre de double-clic, sinon None (le clic simple
        sera confirmé par tick() si rien d'autre n'arrive à temps).
        """
        now = time.perf_counter()
        if self._pending_since is not None and (now - self._pending_since) <= self.double_click_window:
            self._pending_since = None
            return "DOUBLE_CLICK"
        self._pending_since = now
        return None

    def tick(self) -> Optional[str]:
        """À appeler à chaque frame pour confirmer un clic simple une fois
        la fenêtre de double-clic expirée sans second pinch."""
        if self._pending_since is not None and time.perf_counter() - self._pending_since > self.double_click_window:
            self._pending_since = None
            return "LEFT_CLICK"
        return None
