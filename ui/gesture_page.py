"""
Onglet "Gestes" (spec section 20 : mapping gestes -> actions
personnalisable). Le geste PINCH pilote toujours le clic gauche / le
drag — c'est le mécanisme de pointage de base et il n'est pas réassigné
ici. Ce qui reste librement réassignable : le geste deux-doigts et les
quatre directions de swipe (spec section 13, exemple donné dans le
prompt d'origine).
"""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.config_manager import load_gestures_mapping, save_gestures_mapping

logger = logging.getLogger("deku.ui.gestures")

TWO_FINGERS_OPTIONS = [("Clic droit", "right_click"), ("Désactivé", "none")]
SWIPE_OPTIONS = [
    ("Précédent (Alt+Gauche)", "previous"),
    ("Suivant (Alt+Droite)", "next"),
    ("Mission Control (Ctrl+Haut)", "mission_control"),
    ("Afficher le bureau (Win+D)", "show_desktop"),
    ("Désactivé", "none"),
]


def _combo_with_options(options: list[tuple[str, str]]) -> QComboBox:
    combo = QComboBox()
    for label, value in options:
        combo.addItem(label, userData=value)
    return combo


class GesturePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mapping = load_gestures_mapping()
        self._build_ui()
        self._load_into_fields()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(18)

        intro = QLabel(
            "Le pinch (pouce + index) pilote toujours le clic gauche, le "
            "double-clic et le glisser-déposer — c'est le geste de pointage "
            "de base. Les gestes ci-dessous sont personnalisables :"
        )
        intro.setWordWrap(True)
        intro.setObjectName("fieldLabel")
        root.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(14)

        self.two_fingers_combo = _combo_with_options(TWO_FINGERS_OPTIONS)
        form.addRow("✌️  Deux doigts (index + majeur) :", self.two_fingers_combo)

        self.swipe_left_combo = _combo_with_options(SWIPE_OPTIONS)
        form.addRow("👋  Swipe gauche :", self.swipe_left_combo)

        self.swipe_right_combo = _combo_with_options(SWIPE_OPTIONS)
        form.addRow("👋  Swipe droite :", self.swipe_right_combo)

        self.swipe_up_combo = _combo_with_options(SWIPE_OPTIONS)
        form.addRow("👋  Swipe haut :", self.swipe_up_combo)

        self.swipe_down_combo = _combo_with_options(SWIPE_OPTIONS)
        form.addRow("👋  Swipe bas :", self.swipe_down_combo)

        root.addLayout(form)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("divider")
        root.addWidget(divider)

        note = QLabel(
            "🤏 Pinch bref = clic gauche · 🤏🤏 deux pinch rapides = "
            "double-clic · 🤏➡️ pinch maintenu + déplacement = glisser-déposer · "
            "✋ (immobile ~1s) = pause · deux doigts + mouvement vertical = scroll."
        )
        note.setWordWrap(True)
        note.setObjectName("fieldValue")
        root.addWidget(note)

        root.addStretch()

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

    def _select(self, combo: QComboBox, value: str) -> None:
        idx = combo.findData(value)
        combo.setCurrentIndex(max(idx, 0))

    def _load_into_fields(self) -> None:
        self._select(self.two_fingers_combo, self._mapping.get("two_fingers", "right_click"))
        self._select(self.swipe_left_combo, self._mapping.get("swipe_left", "previous"))
        self._select(self.swipe_right_combo, self._mapping.get("swipe_right", "next"))
        self._select(self.swipe_up_combo, self._mapping.get("swipe_up", "mission_control"))
        self._select(self.swipe_down_combo, self._mapping.get("swipe_down", "show_desktop"))

    def _on_save_clicked(self) -> None:
        self._mapping["two_fingers"] = self.two_fingers_combo.currentData()
        self._mapping["swipe_left"] = self.swipe_left_combo.currentData()
        self._mapping["swipe_right"] = self.swipe_right_combo.currentData()
        self._mapping["swipe_up"] = self.swipe_up_combo.currentData()
        self._mapping["swipe_down"] = self.swipe_down_combo.currentData()
        save_gestures_mapping(self._mapping)
        self.saved_label.setText("Mapping enregistré ✓")
        logger.info("Mapping de gestes enregistré : %s", self._mapping)
