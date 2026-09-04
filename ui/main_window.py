"""
Fenêtre principale — Phase 1.

Pipeline actuel : Webcam -> CameraManager -> OpenCV Frame -> affichage Qt.
Aucune reconnaissance de gestes ni contrôle souris/clavier ici (phases
suivantes).

La lecture caméra tourne dans un QThread dédié (CameraWorker) pour ne
jamais bloquer l'interface (spec section 24).
"""
from __future__ import annotations

import logging
import time

import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from camera.camera_manager import CameraError, CameraManager
from camera.camera_settings import CameraSettings
from core.constants import (
    APP_NAME,
    APP_VERSION,
    COLOR_ACCENT,
    COLOR_ACCENT_DARK,
    COLOR_BG,
    COLOR_BG_PANEL,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    LOGO_PATH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)

logger = logging.getLogger("deku.ui")


class CameraWorker(QThread):
    """Boucle de lecture caméra exécutée hors du thread UI."""

    frame_ready = Signal(np.ndarray, float)  # frame BGR, fps instantané
    camera_error = Signal(str)

    MAX_CONSECUTIVE_FAILURES = 30  # ~1s à 30fps avant de considérer une déconnexion

    def __init__(self, camera_manager: CameraManager, parent=None):
        super().__init__(parent)
        self._camera_manager = camera_manager
        self._running = False

    def run(self) -> None:
        self._running = True
        prev_time = time.perf_counter()
        consecutive_failures = 0

        while self._running:
            try:
                ok, frame = self._camera_manager.read_frame()
            except CameraError as exc:
                self.camera_error.emit(str(exc))
                return

            if not ok:
                consecutive_failures += 1
                if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    self.camera_error.emit("La webcam semble déconnectée.")
                    return
                continue

            consecutive_failures = 0
            now = time.perf_counter()
            elapsed = now - prev_time
            prev_time = now
            fps = 1.0 / elapsed if elapsed > 0 else 0.0

            self.frame_ready.emit(frame, fps)

    def stop(self) -> None:
        self._running = False
        self.wait(2000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._camera_manager = CameraManager(CameraSettings())
        self._worker: CameraWorker | None = None

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))

        self._build_ui()
        self._apply_theme()

    # ---------------------------------------------------------- UI
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        # --- En-tête : logo + titre + statut ---
        header = QHBoxLayout()
        header.setSpacing(14)

        if LOGO_PATH.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(LOGO_PATH)).scaledToHeight(
                48, Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(pixmap)
            header.addWidget(logo_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel(APP_NAME.upper())
        title.setObjectName("titleLabel")
        subtitle = QLabel(f"v{APP_VERSION} — Phase 1 : caméra")
        subtitle.setObjectName("subtitleLabel")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.status_label = QLabel("🔴 INACTIVE")
        self.status_label.setObjectName("statusLabel")
        header.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        root.addLayout(header)

        # --- Aperçu vidéo ---
        self.video_label = QLabel("Caméra arrêtée")
        self.video_label.setObjectName("videoLabel")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 400)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.video_label, stretch=1)

        # --- Pied : FPS + bouton Start/Stop ---
        footer = QHBoxLayout()
        self.fps_label = QLabel("FPS : --")
        self.fps_label.setObjectName("fpsLabel")
        footer.addWidget(self.fps_label)
        footer.addStretch()

        self.toggle_button = QPushButton("DÉMARRER")
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        footer.addWidget(self.toggle_button)

        root.addLayout(footer)

        self.setCentralWidget(central)

    def _apply_theme(self) -> None:
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {COLOR_BG}; }}
            QLabel {{ color: {COLOR_TEXT}; font-family: 'Segoe UI', sans-serif; }}
            #titleLabel {{ font-size: 20px; font-weight: 700; letter-spacing: 1px; }}
            #subtitleLabel {{ font-size: 12px; color: {COLOR_TEXT_MUTED}; }}
            #statusLabel {{ font-size: 13px; font-weight: 600; }}
            #fpsLabel {{ font-size: 13px; color: {COLOR_TEXT_MUTED}; }}
            #videoLabel {{
                background-color: {COLOR_BG_PANEL};
                border: 1px solid #2a2f36;
                border-radius: 10px;
                color: {COLOR_TEXT_MUTED};
                font-size: 14px;
            }}
            #toggleButton {{
                background-color: {COLOR_ACCENT};
                color: #06110d;
                font-weight: 700;
                padding: 10px 28px;
                border-radius: 8px;
                border: none;
                font-size: 13px;
                letter-spacing: 1px;
            }}
            #toggleButton:hover {{ background-color: {COLOR_ACCENT_DARK}; }}
            #toggleButton:pressed {{ background-color: {COLOR_ACCENT_DARK}; }}
        """)

    # ---------------------------------------------------------- Contrôle caméra
    def _on_toggle_clicked(self) -> None:
        if self._worker is not None:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self) -> None:
        try:
            self._camera_manager.open()
        except CameraError as exc:
            logger.error("Ouverture caméra échouée : %s", exc)
            self._show_error(str(exc))
            return

        self._worker = CameraWorker(self._camera_manager)
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.camera_error.connect(self._on_camera_error)
        self._worker.start()

        self.toggle_button.setText("ARRÊTER")
        self.status_label.setText("🟢 ACTIVE")

    def _stop_camera(self) -> None:
        if self._worker is not None:
            self._worker.frame_ready.disconnect(self._on_frame_ready)
            self._worker.camera_error.disconnect(self._on_camera_error)
            self._worker.stop()
            self._worker = None

        self._camera_manager.close()
        self.toggle_button.setText("DÉMARRER")
        self.status_label.setText("🔴 INACTIVE")
        self.fps_label.setText("FPS : --")
        self.video_label.setText("Caméra arrêtée")
        self.video_label.setPixmap(QPixmap())

    @Slot(np.ndarray, float)
    def _on_frame_ready(self, frame: np.ndarray, fps: float) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)
        self.fps_label.setText(f"FPS : {fps:.1f}")

    @Slot(str)
    def _on_camera_error(self, message: str) -> None:
        logger.error("Erreur caméra : %s", message)
        self._stop_camera()
        self._show_error(message)

    def _show_error(self, message: str) -> None:
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText(message)
        self.status_label.setText("🔴 ERREUR")

    def closeEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        self._stop_camera()
        super().closeEvent(event)
