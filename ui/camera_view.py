"""
Onglet "Principal" (spec section 18 + Phase 7) : aperçu webcam, statut,
informations de geste, et le CameraWorker qui fait tourner tout le
pipeline (caméra -> vision -> gestes -> curseur -> souris/clavier).

Le mapping gestes -> actions (config/gestures.json) et les paramètres
(config/settings.json) sont relus à chaque clic sur DÉMARRER, donc toute
modification faite dans les onglets Paramètres/Gestes s'applique au
prochain démarrage (spec section 19/20).
"""
from __future__ import annotations

import logging
import threading
import time

import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from camera.camera_manager import CameraError, CameraManager
from camera.camera_settings import CameraSettings
from core.config_manager import load_gestures_mapping, load_settings
from core.constants import (
    DEFAULT_CAMERA_FPS,
    DEFAULT_CAMERA_HEIGHT,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_CAMERA_WIDTH,
    STATUS_ACTIVE,
    STATUS_ERROR,
    STATUS_INFO,
    STATUS_PAUSED,
)
from cursor.cursor_controller import CursorController
from gestures.gesture_engine import GestureEngine, GestureSnapshot
from input.keyboard_controller import KeyboardController
from input.mouse_controller import MouseController
from input.system_controller import SystemController
from vision.hand_tracker import INDEX_TIP, HandTracker, draw_landmarks

logger = logging.getLogger("deku.ui.camera_view")


class StatusChip(QWidget):
    """Badge de statut façon charte graphique : pastille colorée + texte."""

    def __init__(self, text: str = "", color: str = STATUS_INFO, parent=None):
        super().__init__(parent)
        self.setObjectName("statusChip")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 14, 4)
        layout.setSpacing(7)

        self._dot = QLabel("●")
        self._dot.setObjectName("chipDot")
        self._label = QLabel(text)
        self._label.setObjectName("chipLabel")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        self.set_status(text, color)

    def set_status(self, text: str, color: str) -> None:
        self._label.setText(text)
        self._dot.setStyleSheet(f"color: {color}; font-size: 11px;")


class CameraWorker(QThread):
    """Lit les frames, exécute le suivi de main + les gestes + le curseur
    + les actions souris/clavier, hors du thread UI (spec section 24)."""

    frame_ready = Signal(np.ndarray, float, object, object)  # frame, fps, GestureSnapshot, cursor_pos
    camera_error = Signal(str)
    paused_changed = Signal(bool)

    MAX_CONSECUTIVE_FAILURES = 30

    def __init__(self, camera_manager: CameraManager, settings: dict, gestures_mapping: dict, parent=None):
        super().__init__(parent)
        self._camera_manager = camera_manager
        self._settings = settings
        self._gestures_mapping = gestures_mapping
        self._running = False
        self._paused = threading.Event()

    def toggle_pause(self) -> None:
        """Bascule le mode pause (spec section 17). Thread-safe : peut être
        appelée depuis le thread UI, le raccourci global, ou ce thread."""
        if self._paused.is_set():
            self._paused.clear()
        else:
            self._paused.set()
        self.paused_changed.emit(self._paused.is_set())

    @property
    def is_paused(self) -> bool:
        return self._paused.is_set()

    def run(self) -> None:
        self._running = True
        prev_time = time.perf_counter()
        consecutive_failures = 0

        gest_cfg = self._settings.get("gestures", {})
        cursor_cfg = self._settings.get("cursor", {})

        try:
            hand_tracker = HandTracker(
                num_hands=1,
                min_detection_confidence=gest_cfg.get("confidence_threshold", 0.6),
            )
        except Exception as exc:
            logger.error("Initialisation du suivi de main impossible : %s", exc)
            self.camera_error.emit(str(exc))
            return

        gesture_engine = GestureEngine(
            pinch_min_hold=gest_cfg.get("min_hold_duration", 0.05),
            pinch_cooldown=gest_cfg.get("click_cooldown", 0.3),
        )
        mouse_controller = MouseController()
        keyboard_controller = KeyboardController()
        cursor_controller = CursorController(
            mouse_controller=mouse_controller,
            sensitivity=cursor_cfg.get("sensitivity", 1.0),
            smoothing_strength=cursor_cfg.get("smoothing", 0.5),
            dead_zone=cursor_cfg.get("dead_zone", 0.02),
        )
        system_controller = SystemController(on_toggle_pause=self.toggle_pause)
        system_controller.start()

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

                snapshot = gesture_engine.process(hand_data, frame_width, frame_height, timestamp=now)

                cursor_pos = None
                if hand_data is not None and hand_data.is_valid:
                    draw_landmarks(frame, hand_data)
                    if not self._paused.is_set():
                        index_x, index_y, _ = hand_data.landmarks[INDEX_TIP]
                        cursor_pos = cursor_controller.update(index_x, index_y)
                else:
                    cursor_controller.reset()

                if snapshot.action == "PAUSE_TOGGLE":
                    self.toggle_pause()
                elif not self._paused.is_set():
                    self._dispatch_action(snapshot, mouse_controller, keyboard_controller)

                self.frame_ready.emit(frame, fps, snapshot, cursor_pos)
        finally:
            system_controller.stop()
            hand_tracker.close()

    def _dispatch_action(self, snapshot: GestureSnapshot, mouse: MouseController, keyboard: KeyboardController) -> None:
        action = snapshot.action
        mapping = self._gestures_mapping

        if action == "LEFT_CLICK":
            logger.info("Action : clic gauche")
            mouse.left_click()
        elif action == "DOUBLE_CLICK":
            logger.info("Action : double-clic")
            mouse.double_click()
        elif action == "RIGHT_CLICK":
            if mapping.get("two_fingers", "right_click") != "none":
                logger.info("Action : clic droit")
                mouse.right_click()
        elif action == "DRAG_START":
            logger.info("Action : début du drag")
            mouse.drag_start()
        elif action == "DRAG_END":
            logger.info("Action : fin du drag")
            mouse.drag_end()
        elif action == "SCROLL":
            if mapping.get("two_fingers_vertical", "scroll") != "none":
                mouse.scroll(snapshot.action_value)
        elif action in ("SWIPE_LEFT", "SWIPE_RIGHT", "SWIPE_UP", "SWIPE_DOWN"):
            action_name = mapping.get(action.lower(), "none")
            if keyboard.trigger_named(action_name):
                logger.info("Action : %s -> %s", action, action_name)
        # DRAG_MOVE : rien à faire, le déplacement continu du curseur suffit.

    def stop(self) -> None:
        self._running = False
        self.wait(2000)


class CameraView(QWidget):
    """Widget de l'onglet Principal : caméra, statut, gestes, debug."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: CameraWorker | None = None
        self._debug_enabled = False
        self._build_ui()

    # ---------------------------------------------------------- UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        # --- Barre de statut ---
        status_bar = QHBoxLayout()
        self.status_chip = StatusChip("INACTIF", STATUS_ERROR)
        status_bar.addWidget(self.status_chip)
        status_bar.addStretch()
        self.fps_label = QLabel("FPS : --")
        self.fps_label.setObjectName("infoLabel")
        status_bar.addWidget(self.fps_label)
        root.addLayout(status_bar)

        # --- Aperçu vidéo ---
        self.video_label = QLabel("Caméra arrêtée")
        self.video_label.setObjectName("videoLabel")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 380)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.video_label, stretch=1)

        # --- Barre d'info main/geste/action ---
        info_bar = QHBoxLayout()
        self.hand_label = QLabel("Main : —")
        self.hand_label.setObjectName("infoLabel")
        self.gesture_label = QLabel("Geste : —")
        self.gesture_label.setObjectName("infoLabel")
        self.action_label = QLabel("Action : —")
        self.action_label.setObjectName("infoLabel")
        for w in (self.hand_label, self.gesture_label, self.action_label):
            info_bar.addWidget(w)
            info_bar.addStretch()
        root.addLayout(info_bar)

        # --- Panneau debug (spec section 22), masqué par défaut ---
        self.debug_label = QLabel("")
        self.debug_label.setObjectName("debugPanel")
        self.debug_label.setVisible(False)
        self.debug_label.setWordWrap(True)
        root.addWidget(self.debug_label)

        # --- Pied : boutons ---
        footer = QHBoxLayout()
        footer.addStretch()

        self.pause_button = QPushButton("PAUSE")
        self.pause_button.setObjectName("secondaryButton")
        self.pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        footer.addWidget(self.pause_button)

        self.toggle_button = QPushButton("DÉMARRER")
        self.toggle_button.setObjectName("primaryButton")
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        footer.addWidget(self.toggle_button)

        root.addLayout(footer)

    def set_debug_enabled(self, enabled: bool) -> None:
        self._debug_enabled = enabled
        self.debug_label.setVisible(enabled)

    # ---------------------------------------------------------- Contrôle
    def _on_toggle_clicked(self) -> None:
        if self._worker is not None:
            self._stop_camera()
        else:
            self._start_camera()

    def _on_pause_clicked(self) -> None:
        if self._worker is not None:
            self._worker.toggle_pause()

    def _start_camera(self) -> None:
        settings = load_settings()
        gestures_mapping = load_gestures_mapping()
        cam_cfg = settings.get("camera", {})

        camera_settings = CameraSettings(
            device_index=cam_cfg.get("device", DEFAULT_CAMERA_INDEX),
            width=cam_cfg.get("width", DEFAULT_CAMERA_WIDTH),
            height=cam_cfg.get("height", DEFAULT_CAMERA_HEIGHT),
            fps=cam_cfg.get("fps", DEFAULT_CAMERA_FPS),
        )
        camera_manager = CameraManager(camera_settings)

        try:
            camera_manager.open()
        except CameraError as exc:
            logger.error("Ouverture caméra échouée : %s", exc)
            self._show_error(str(exc))
            return

        self._worker = CameraWorker(camera_manager, settings, gestures_mapping)
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.camera_error.connect(self._on_camera_error)
        self._worker.paused_changed.connect(self._on_paused_changed)
        self._worker.start()

        self.toggle_button.setText("ARRÊTER")
        self.pause_button.setEnabled(True)
        self.status_chip.set_status("ACTIF", STATUS_ACTIVE)
        logger.info("Contrôle gestuel activé (curseur + clics + scroll + swipes).")

    def _stop_camera(self) -> None:
        if self._worker is not None:
            self._worker.frame_ready.disconnect(self._on_frame_ready)
            self._worker.camera_error.disconnect(self._on_camera_error)
            self._worker.paused_changed.disconnect(self._on_paused_changed)
            self._worker.stop()
            self._worker = None

        self.toggle_button.setText("DÉMARRER")
        self.pause_button.setEnabled(False)
        self.pause_button.setText("PAUSE")
        self.status_chip.set_status("INACTIF", STATUS_ERROR)
        self.fps_label.setText("FPS : --")
        self.hand_label.setText("Main : —")
        self.gesture_label.setText("Geste : —")
        self.action_label.setText("Action : —")
        self.debug_label.setText("")
        self.video_label.setText("Caméra arrêtée")
        self.video_label.setPixmap(QPixmap())

    @Slot(bool)
    def _on_paused_changed(self, paused: bool) -> None:
        if paused:
            self.status_chip.set_status("EN PAUSE", STATUS_PAUSED)
            self.pause_button.setText("REPRENDRE")
        else:
            self.status_chip.set_status("ACTIF", STATUS_ACTIVE)
            self.pause_button.setText("PAUSE")

    @Slot(np.ndarray, float, object, object)
    def _on_frame_ready(self, frame: np.ndarray, fps: float, snapshot: GestureSnapshot, cursor_pos) -> None:
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

        if self._debug_enabled:
            index_px = snapshot.index_tip_px or ("--", "--")
            thumb_px = snapshot.thumb_tip_px or ("--", "--")
            cursor_txt = f"X={cursor_pos[0]:.0f} Y={cursor_pos[1]:.0f}" if cursor_pos else "—"
            paused_txt = "OUI" if (self._worker and self._worker.is_paused) else "NON"
            self.debug_label.setText(
                f"FPS: {fps:.1f}\n"
                f"Hands: {1 if snapshot.hand_detected else 0}\n"
                f"Confidence: {snapshot.confidence * 100:.0f}%\n"
                f"Index: X={index_px[0]} Y={index_px[1]}\n"
                f"Thumb: X={thumb_px[0]} Y={thumb_px[1]}\n"
                f"Gesture: {snapshot.gesture_name}\n"
                f"State: {snapshot.state_name}\n"
                f"Cursor: {cursor_txt}\n"
                f"Action: {snapshot.action or '—'}\n"
                f"Paused: {paused_txt}"
            )

    @Slot(str)
    def _on_camera_error(self, message: str) -> None:
        logger.error("Erreur caméra : %s", message)
        self._stop_camera()
        self._show_error(message)

    def _show_error(self, message: str) -> None:
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText(message)
        self.status_chip.set_status("ERREUR", STATUS_ERROR)

    def shutdown(self) -> None:
        """À appeler à la fermeture de la fenêtre."""
        self._stop_camera()
