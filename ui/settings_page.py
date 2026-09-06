"""
Onglet "Paramètres" (spec section 19 : caméra, curseur, gestes,
interface) + sélecteur de profils (spec section 21).

Toutes les valeurs sont sauvegardées dans config/settings.json (et
config/profiles.json pour les profils) via core.config_manager. Les
changements s'appliquent au prochain DÉMARRER de la caméra (thème et
mode debug exceptés, qui s'appliquent immédiatement).
"""
from __future__ import annotations

import copy
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from camera.camera_manager import CameraManager
from core.config_manager import (
    apply_profile_overrides,
    load_gestures_mapping,
    load_profiles,
    load_settings,
    save_gestures_mapping,
    save_settings,
)

logger = logging.getLogger("deku.ui.settings")

RESOLUTIONS = [("640 x 480", 640, 480), ("1280 x 720 (recommandé)", 1280, 720), ("1920 x 1080", 1920, 1080)]
PROFILE_LABELS = {
    "default": "Défaut",
    "gaming": "Gaming",
    "presentation": "Présentation",
    "browsing": "Navigation web",
}


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def _slider_row(label_text: str, minimum: int, maximum: int, value: int, suffix: str = "") -> tuple[QWidget, QSlider, QLabel]:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(label_text)
    label.setObjectName("fieldLabel")
    label.setMinimumWidth(170)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(minimum)
    slider.setMaximum(maximum)
    slider.setValue(value)
    value_label = QLabel(f"{value}{suffix}")
    value_label.setObjectName("fieldValue")
    value_label.setMinimumWidth(50)
    slider.valueChanged.connect(lambda v: value_label.setText(f"{v}{suffix}"))
    layout.addWidget(label)
    layout.addWidget(slider, stretch=1)
    layout.addWidget(value_label)
    return row, slider, value_label


class SettingsPage(QWidget):
    theme_changed = Signal(str)
    debug_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = load_settings()
        self._profiles = load_profiles()
        self._build_ui()
        self._load_into_fields(self._settings)

    # ---------------------------------------------------------- UI
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setSpacing(18)
        root.setContentsMargins(4, 4, 4, 4)

        # --- Profils ---
        root.addWidget(_section_title("PROFIL"))
        profile_row = QHBoxLayout()
        self.profile_combo = QComboBox()
        for key in self._profiles.keys():
            self.profile_combo.addItem(PROFILE_LABELS.get(key, key), userData=key)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        profile_row.addWidget(self.profile_combo, stretch=1)
        root.addLayout(profile_row)
        root.addWidget(self._divider())

        # --- Caméra ---
        root.addWidget(_section_title("CAMÉRA"))
        cam_row = QHBoxLayout()
        cam_row.addWidget(QLabel("Périphérique :"))
        self.device_combo = QComboBox()
        self._populate_devices()
        cam_row.addWidget(self.device_combo, stretch=1)
        root.addLayout(cam_row)

        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Résolution :"))
        self.resolution_combo = QComboBox()
        for label, w, h in RESOLUTIONS:
            self.resolution_combo.addItem(label, userData=(w, h))
        res_row.addWidget(self.resolution_combo, stretch=1)
        root.addLayout(res_row)

        fps_row = QHBoxLayout()
        fps_row.addWidget(QLabel("FPS cible :"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        fps_row.addWidget(self.fps_spin, stretch=1)
        root.addLayout(fps_row)
        root.addWidget(self._divider())

        # --- Curseur ---
        root.addWidget(_section_title("CURSEUR"))
        sens_row, self.sensitivity_slider, _ = _slider_row("Sensibilité", 50, 200, 100)
        smooth_row, self.smoothing_slider, _ = _slider_row("Lissage", 0, 95, 50)
        dead_row, self.dead_zone_slider, _ = _slider_row("Zone morte", 0, 10, 2)
        for r in (sens_row, smooth_row, dead_row):
            root.addWidget(r)
        root.addWidget(self._divider())

        # --- Gestes ---
        root.addWidget(_section_title("GESTES"))
        conf_row, self.confidence_slider, _ = _slider_row("Seuil de confiance", 30, 90, 60)
        hold_row, self.min_hold_slider, _ = _slider_row("Durée minimale (ms)", 0, 300, 50)
        cooldown_row, self.cooldown_slider, _ = _slider_row("Cooldown (ms)", 100, 1000, 300)
        for r in (conf_row, hold_row, cooldown_row):
            root.addWidget(r)
        root.addWidget(self._divider())

        # --- Interface ---
        root.addWidget(_section_title("INTERFACE"))
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Thème :"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Sombre", userData="dark")
        self.theme_combo.addItem("Clair", userData="light")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo, stretch=1)
        root.addLayout(theme_row)

        self.debug_checkbox = QCheckBox("Mode debug (coordonnées, FPS détaillé, état des gestes)")
        self.debug_checkbox.toggled.connect(self.debug_toggled.emit)
        root.addWidget(self.debug_checkbox)

        root.addStretch()

        # --- Enregistrer ---
        save_row = QHBoxLayout()
        save_row.addStretch()
        self.save_button = QPushButton("ENREGISTRER")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self._on_save_clicked)
        save_row.addWidget(self.save_button)
        self.saved_label = QLabel("")
        self.saved_label.setObjectName("fieldValue")
        save_row.addWidget(self.saved_label)
        root.addLayout(save_row)

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("divider")
        return line

    def _populate_devices(self) -> None:
        try:
            available = CameraManager().list_available_cameras()
        except Exception:
            available = []
        if not available:
            available = [0]
        for index in available:
            self.device_combo.addItem(f"Caméra {index}", userData=index)

    # ---------------------------------------------------------- Chargement / sauvegarde
    def _load_into_fields(self, settings: dict) -> None:
        cam = settings.get("camera", {})
        cursor = settings.get("cursor", {})
        gest = settings.get("gestures", {})
        interface = settings.get("interface", {})

        device_idx = self.device_combo.findData(cam.get("device", 0))
        self.device_combo.setCurrentIndex(max(device_idx, 0))

        target_res = (cam.get("width", 1280), cam.get("height", 720))
        for i in range(self.resolution_combo.count()):
            if self.resolution_combo.itemData(i) == target_res:
                self.resolution_combo.setCurrentIndex(i)
                break

        self.fps_spin.setValue(cam.get("fps", 30))
        self.sensitivity_slider.setValue(int(cursor.get("sensitivity", 1.0) * 100))
        self.smoothing_slider.setValue(int(cursor.get("smoothing", 0.5) * 100))
        self.dead_zone_slider.setValue(int(cursor.get("dead_zone", 0.02) * 100))
        self.confidence_slider.setValue(int(gest.get("confidence_threshold", 0.6) * 100))
        self.min_hold_slider.setValue(int(gest.get("min_hold_duration", 0.05) * 1000))
        self.cooldown_slider.setValue(int(gest.get("click_cooldown", 0.3) * 1000))

        theme_idx = self.theme_combo.findData(interface.get("theme", "dark"))
        self.theme_combo.setCurrentIndex(max(theme_idx, 0))

    def _collect_from_fields(self) -> dict:
        width, height = self.resolution_combo.currentData()
        return {
            "camera": {
                "device": self.device_combo.currentData(),
                "width": width,
                "height": height,
                "fps": self.fps_spin.value(),
            },
            "cursor": {
                "sensitivity": self.sensitivity_slider.value() / 100,
                "smoothing": self.smoothing_slider.value() / 100,
                "dead_zone": self.dead_zone_slider.value() / 100,
            },
            "gestures": {
                "confidence_threshold": self.confidence_slider.value() / 100,
                "min_hold_duration": self.min_hold_slider.value() / 1000,
                "click_cooldown": self.cooldown_slider.value() / 1000,
            },
            "interface": {"theme": self.theme_combo.currentData()},
        }

    def _on_theme_changed(self) -> None:
        self.theme_changed.emit(self.theme_combo.currentData())

    def _on_profile_selected(self) -> None:
        key = self.profile_combo.currentData()
        profile = self._profiles.get(key, {})
        settings = copy.deepcopy(self._settings)
        gestures_mapping = load_gestures_mapping()
        apply_profile_overrides(settings, gestures_mapping, profile)
        self._load_into_fields(settings)
        save_settings(settings)
        save_gestures_mapping(gestures_mapping)
        self._settings = settings
        self.saved_label.setText(f"Profil « {PROFILE_LABELS.get(key, key)} » appliqué")

    def _on_save_clicked(self) -> None:
        settings = self._collect_from_fields()
        save_settings(settings)
        self._settings = settings
        self.saved_label.setText("Paramètres enregistrés ✓")
        logger.info("Paramètres enregistrés.")
