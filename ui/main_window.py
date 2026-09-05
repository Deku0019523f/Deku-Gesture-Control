"""
Fenêtre principale — Phases 1 à 4.

Pipeline : Webcam -> CameraManager -> OpenCV Frame -> HandTracker (MediaPipe)
-> HandData -> Landmark Processor -> Hand Geometry -> Gesture Engine (pinch)
-> affichage ; en parallèle, Index -> Cursor Controller -> Mouse Controller
-> curseur système réel (spec section 4/29).

Aucun clic, drag, scroll ni raccourci clavier n'est encore déclenché
(Phase 5+). La lecture caméra + tout le traitement tournent dans un
QThread dédié (CameraWorker) pour ne jamais bloquer l'UI (spec section 24).
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
from cursor.cursor_controller import CursorController
from gestures.gesture_engine import GestureEngine, GestureSnapshot
from input.mouse_controller import MouseController
from vision.hand_tracker import INDEX_TIP, HandTracker, draw_landmarks

logger = logging.getLogger("deku.ui")


class CameraWorker(QThread):
    """Lit les frames, exécute le suivi de main + les gestes + le curseur,
    hors du thread UI."""

    frame_ready = Signal(np.ndarray, float, object)  # frame BGR annotée, fps, GestureSnapshot
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

        try:
            hand_tracker = HandTracker(num_hands=1)
        except Exception as exc:  # modèle absent, pas d'Internet, etc.
            logger.error("Initialisation du suivi de main impossible : %s", exc)
            self.camera_error.emit(str(exc))
            return

        gesture_engine = GestureEngine()
        mouse_controller = MouseController()
        cursor_controller = CursorController(mouse_controller=mouse_controller)

        try:
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

                frame_height, frame_width = frame.shape[:2]
                hands = hand_tracker.process(frame)
                hand_data = hands[0] if hands else None

                snapshot = gesture_engine.process(hand_data, frame_width, frame_height)

                if hand_data is not None and hand_data.is_valid:
                    draw_landmarks(frame, hand_data)
                    index_x, index_y, _ = hand_data.landmarks[INDEX_TIP]
                    cursor_controller.update(index_x, index_y)
                else:
                    cursor_controller.reset()

                if snapshot.action == "LEFT_CLICK":
                    logger.info("Action : clic gauche")
                    mouse_controller.left_click()
                elif snapshot.action == "DOUBLE_CLICK":
                    logger.info("Action : double-clic")
                    mouse_controller.double_click()
                elif snapshot.action == "RIGHT_CLICK":
                    logger.info("Action : clic droit")
                    mouse_controller.right_click()
                elif snapshot.action == "DRAG_START":
                    logger.info("Action : début du drag")
                    mouse_controller.drag_start()
                elif snapshot.action == "DRAG_END":
                    logger.info("Action : fin du drag")
                    mouse_controller.drag_end()
                # DRAG_MOVE : rien à faire ici, le déplacement continu du
                # curseur ci-dessus suffit pendant que le bouton est maintenu.

                self.frame_ready.emit(frame, fps, snapshot)
        finally:
            hand_tracker.close()

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
        root.setSpacing(14)

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
        subtitle = QLabel(f"v{APP_VERSION} — Phases 1 à 5 : caméra, main, gestes, curseur, clics")
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
        self.video_label.setMinimumSize(640, 380)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.video_label, stretch=1)

        # --- Barre d'info main/geste ---
        info_bar = QHBoxLayout()
        self.hand_label = QLabel("Main : —")
        self.hand_label.setObjectName("infoLabel")
        self.gesture_label = QLabel("Geste : —")
        self.gesture_label.setObjectName("infoLabel")
        info_bar.addWidget(self.hand_label)
        info_bar.addStretch()
        info_bar.addWidget(self.gesture_label)
        info_bar.addStretch()
        self.action_label = QLabel("Action : —")
        self.action_label.setObjectName("infoLabel")
        info_bar.addWidget(self.action_label)
        root.addLayout(info_bar)

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
            #infoLabel {{ font-size: 13px; color: {COLOR_TEXT_MUTED}; }}
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
        logger.info("Contrôle du curseur par l'index activé.")

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
        self.hand_label.setText("Main : —")
        self.gesture_label.setText("Geste : —")
        self.action_label.setText("Action : —")
        self.video_label.setText("Caméra arrêtée")
        self.video_label.setPixmap(QPixmap())

    @Slot(np.ndarray, float, object)
    def _on_frame_ready(self, frame: np.ndarray, fps: float, snapshot: GestureSnapshot) -> None:
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

        if snapshot.hand_detected:
            self.hand_label.setText(
                f"Main : 🟢 détectée ({snapshot.confidence * 100:.0f}%) — ouverture {snapshot.hand_openness * 100:.0f}%"
            )
            self.gesture_label.setText(f"Geste : {snapshot.gesture_name} — {snapshot.state_name}")
        else:
            self.hand_label.setText("Main : ⚪ non détectée")
            self.gesture_label.setText("Geste : —")

        if snapshot.action:
            self.action_label.setText(f"Action : {snapshot.action}")

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
