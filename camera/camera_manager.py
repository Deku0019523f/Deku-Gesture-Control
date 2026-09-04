"""
CameraManager (spec section 5) : seule couche du programme qui parle
directement à OpenCV pour accéder à la webcam.

Tout le traitement reste local à la machine : aucune frame n'est jamais
écrite sur disque ni envoyée sur le réseau (spec section 28).
"""
from __future__ import annotations

import logging
import platform
from typing import List, Optional, Tuple

import cv2
import numpy as np

from camera.camera_settings import CameraSettings
from core.constants import MAX_CAMERA_PROBE_INDEX

logger = logging.getLogger("deku.camera")


class CameraError(Exception):
    """Erreur caméra : introuvable, déjà utilisée, déconnectée, etc."""


class CameraManager:
    """Possède le cycle de vie d'une webcam."""

    def __init__(self, settings: Optional[CameraSettings] = None):
        self.settings = settings or CameraSettings()
        self._capture: Optional[cv2.VideoCapture] = None

    # ---------------------------------------------------------- Découverte
    def list_available_cameras(self, max_index: int = MAX_CAMERA_PROBE_INDEX) -> List[int]:
        """Teste les index 0..max_index-1 et renvoie ceux qui s'ouvrent."""
        available = []
        backend = self._preferred_backend()
        for index in range(max_index):
            cap = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)
            if cap is not None and cap.isOpened():
                available.append(index)
            if cap is not None:
                cap.release()
        logger.info("Webcams détectées : %s", available)
        return available

    @staticmethod
    def _preferred_backend():
        # DirectShow est plus fiable sur Windows (cible principale du projet).
        if platform.system() == "Windows":
            return cv2.CAP_DSHOW
        return None

    # ---------------------------------------------------------- Cycle de vie
    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self, device_index: Optional[int] = None) -> None:
        """Ouvre la webcam. Lève CameraError avec un message clair en cas d'échec."""
        if self.is_opened():
            self.close()

        index = device_index if device_index is not None else self.settings.device_index
        backend = self._preferred_backend()
        capture = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)

        if not capture.isOpened():
            capture.release()
            raise CameraError(
                f"Impossible d'ouvrir la caméra {index}. "
                "Aucune webcam disponible, ou elle est utilisée par une autre application."
            )

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
        capture.set(cv2.CAP_PROP_FPS, self.settings.fps)

        self._capture = capture
        self.settings.device_index = index
        logger.info(
            "Caméra %s ouverte (%sx%s @ %sfps demandés)",
            index, self.settings.width, self.settings.height, self.settings.fps,
        )

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            logger.info("Caméra fermée.")

    # ---------------------------------------------------------- Frames
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Lit une frame. Retourne (succès, frame_bgr_ou_None).

        Ne lève jamais pour un échec ponctuel (glitch transitoire) : c'est à
        l'appelant de décider combien d'échecs consécutifs signifient une
        déconnexion réelle.
        """
        if not self.is_opened():
            raise CameraError("La caméra n'est pas ouverte.")

        ok, frame = self._capture.read()
        if not ok or frame is None:
            logger.warning("Échec de lecture d'une frame caméra.")
            return False, None
        return True, frame

    # ---------------------------------------------------------- Configuration
    def set_resolution(self, width: int, height: int) -> None:
        self.settings.width = width
        self.settings.height = height
        if self.is_opened():
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def set_fps(self, fps: int) -> None:
        self.settings.fps = fps
        if self.is_opened():
            self._capture.set(cv2.CAP_PROP_FPS, fps)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
