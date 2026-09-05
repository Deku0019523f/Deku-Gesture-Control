"""
HandTracker : abstraction au-dessus de MediaPipe (spec section 6).

Le reste du programme ne manipule jamais les objets internes de MediaPipe,
seulement des HandData. Cela isole le reste du code d'un éventuel
changement d'API côté MediaPipe.

Note technique : la version actuelle de MediaPipe n'expose plus l'ancienne
API `mp.solutions.hands` — ce module utilise donc l'API Tasks
(`mediapipe.tasks.python.vision.HandLandmarker`), qui nécessite un fichier
modèle `hand_landmarker.task` téléchargé une seule fois (voir
`ensure_model_downloaded`).
"""
from __future__ import annotations

import logging
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from core.constants import ASSETS_DIR

logger = logging.getLogger("deku.vision")

MODEL_DIR = ASSETS_DIR / "models"
MODEL_PATH = MODEL_DIR / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

# Index MediaPipe des 21 landmarks de la main (spec section 6/7)
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20


@dataclass
class HandData:
    """Représentation neutre d'une main détectée, indépendante de MediaPipe."""

    landmarks: List[Tuple[float, float, float]]  # (x, y, z) normalisés 0..1
    confidence: float
    handedness: str  # "Left" ou "Right"
    bounding_box: Tuple[float, float, float, float]  # xmin, ymin, xmax, ymax

    @property
    def is_valid(self) -> bool:
        return len(self.landmarks) == 21


def ensure_model_downloaded() -> Path:
    """Télécharge hand_landmarker.task s'il est absent (spec section 2).

    Nécessite une connexion Internet uniquement lors du tout premier
    lancement ; le modèle reste ensuite en cache dans assets/models/.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        return MODEL_PATH

    logger.info("Téléchargement du modèle hand_landmarker.task...")
    tmp_path = MODEL_PATH.with_suffix(".tmp")
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp_path)
        tmp_path.rename(MODEL_PATH)
        logger.info("Modèle téléchargé : %s", MODEL_PATH)
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            "Impossible de télécharger le modèle de détection de main "
            f"({exc}). Vérifiez votre connexion Internet, ou téléchargez-le "
            f"manuellement depuis {MODEL_URL} vers {MODEL_PATH}."
        ) from exc
    return MODEL_PATH


class HandTracker:
    """Détecte une main dans une frame BGR OpenCV et renvoie des HandData."""

    def __init__(
        self,
        num_hands: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
        model_path: Optional[Path] = None,
    ):
        resolved_model = model_path or ensure_model_downloaded()

        base_options = mp_python.BaseOptions(model_asset_path=str(resolved_model))
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
        self._start_time = time.perf_counter()

    def process(self, frame_bgr: np.ndarray) -> List[HandData]:
        """Traite une frame et renvoie la liste des mains détectées."""
        rgb = np.ascontiguousarray(frame_bgr[:, :, ::-1])  # BGR -> RGB, en mémoire
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.perf_counter() - self._start_time) * 1000)

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        hands: List[HandData] = []
        if not result.hand_landmarks:
            return hands

        for i, landmark_list in enumerate(result.hand_landmarks):
            points = [(lm.x, lm.y, lm.z) for lm in landmark_list]
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]

            handedness = "?"
            confidence = 0.0
            if i < len(result.handedness) and result.handedness[i]:
                top = result.handedness[i][0]
                handedness = top.category_name
                confidence = top.score

            hands.append(
                HandData(
                    landmarks=points,
                    confidence=confidence,
                    handedness=handedness,
                    bounding_box=(min(xs), min(ys), max(xs), max(ys)),
                )
            )
        return hands

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()


def draw_landmarks(
    frame_bgr: np.ndarray, hand_data: HandData, color: Tuple[int, int, int] = (168, 224, 34)
) -> np.ndarray:
    """Dessine les 21 landmarks et leurs connexions sur la frame (spec section 6/22)."""
    h, w = frame_bgr.shape[:2]
    points_px = [(int(x * w), int(y * h)) for x, y, _ in hand_data.landmarks]

    for connection in mp_vision.HandLandmarksConnections.HAND_CONNECTIONS:
        cv2.line(frame_bgr, points_px[connection.start], points_px[connection.end], color, 2)

    for point in points_px:
        cv2.circle(frame_bgr, point, 4, color, -1)

    return frame_bgr
