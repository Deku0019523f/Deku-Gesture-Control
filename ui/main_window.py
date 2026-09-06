"""
Fenêtre principale (spec section 18, Phase 7) : assemble les onglets
Principal / Paramètres / Gestes dans une interface stylée selon la
charte graphique officielle du projet (couleurs, typographies Poppins /
Inter, boutons pilule, badges de statut).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from core.config_manager import load_settings
from core.constants import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    DEFAULT_THEME,
    FONT_BODY,
    FONT_HEADING,
    LOGO_PATH,
    THEMES,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from ui.camera_view import CameraView
from ui.gesture_page import GesturePage
from ui.settings_page import SettingsPage


def _build_stylesheet(theme_name: str) -> str:
    t = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    return f"""
        QMainWindow, QWidget {{
            background-color: {t['bg']};
            color: {t['text']};
            font-family: '{FONT_BODY}';
            font-size: 13px;
        }}
        QTabWidget::pane {{
            border: 1px solid {t['border']};
            border-radius: 10px;
            background-color: {t['bg_panel']};
            top: -1px;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {t['text_muted']};
            font-family: '{FONT_HEADING}';
            font-weight: 600;
            padding: 10px 22px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        QTabBar::tab:selected {{
            color: {t['accent']};
            background-color: {t['bg_panel']};
            border-bottom: 2px solid {t['accent']};
        }}
        QTabBar::tab:hover {{ color: {t['text']}; }}

        #titleLabel {{
            font-family: '{FONT_HEADING}';
            font-size: 21px;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        #subtitleLabel {{
            font-family: '{FONT_BODY}';
            font-size: 11px;
            color: {t['text_muted']};
            letter-spacing: 0.5px;
        }}
        #sectionTitle {{
            font-family: '{FONT_HEADING}';
            font-size: 13px;
            font-weight: 600;
            color: {t['accent']};
            letter-spacing: 1px;
            margin-top: 6px;
        }}
        #fieldLabel {{ color: {t['text_muted']}; }}
        #fieldValue {{ color: {t['text_muted']}; font-size: 12px; }}
        #divider {{ background-color: {t['border']}; max-height: 1px; border: none; }}

        #videoLabel {{
            background-color: {t['bg']};
            border: 1px solid {t['border']};
            border-radius: 12px;
            color: {t['text_muted']};
            font-size: 14px;
        }}
        #infoLabel {{ color: {t['text_muted']}; font-size: 13px; }}
        #debugPanel {{
            background-color: {t['bg']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 10px;
            color: {t['text_muted']};
            font-size: 12px;
        }}

        #statusChip {{
            background-color: {t['bg']};
            border: 1px solid {t['border']};
            border-radius: 14px;
        }}
        #chipLabel {{ font-weight: 600; font-size: 12px; color: {t['text']}; }}

        #primaryButton {{
            background-color: {t['accent']};
            color: {t['accent_text']};
            font-family: '{FONT_HEADING}';
            font-weight: 700;
            padding: 10px 30px;
            border-radius: 18px;
            border: none;
            font-size: 13px;
            letter-spacing: 0.5px;
        }}
        #primaryButton:hover {{ background-color: {t['accent_dark']}; }}
        #primaryButton:pressed {{ background-color: {t['accent_dark']}; }}
        #primaryButton:disabled {{ background-color: {t['border']}; color: {t['text_muted']}; }}

        #secondaryButton {{
            background-color: transparent;
            color: {t['accent']};
            font-family: '{FONT_HEADING}';
            font-weight: 600;
            padding: 9px 24px;
            border-radius: 18px;
            border: 1.5px solid {t['accent']};
            font-size: 13px;
        }}
        #secondaryButton:hover {{ background-color: rgba(0, 230, 184, 0.12); }}
        #secondaryButton:disabled {{ color: {t['text_muted']}; border-color: {t['border']}; }}

        QComboBox, QSpinBox {{
            background-color: {t['bg']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            padding: 5px 8px;
            color: {t['text']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {t['bg_panel']};
            color: {t['text']};
            selection-background-color: {t['accent']};
            selection-color: {t['accent_text']};
        }}
        QSlider::groove:horizontal {{ height: 4px; background: {t['border']}; border-radius: 2px; }}
        QSlider::handle:horizontal {{
            background: {t['accent']}; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 2px; }}
        QCheckBox {{ color: {t['text']}; }}
        QScrollArea {{ border: none; background: transparent; }}
    """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))

        self._theme = load_settings().get("interface", {}).get("theme", DEFAULT_THEME)
        self._build_ui()
        self.apply_theme(self._theme)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # --- En-tête : logo + titre + accroche de marque ---
        header = QHBoxLayout()
        header.setSpacing(14)
        if LOGO_PATH.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(LOGO_PATH)).scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            header.addWidget(logo_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel(APP_NAME.upper())
        title.setObjectName("titleLabel")
        subtitle = QLabel(f"v{APP_VERSION} — {APP_TAGLINE}")
        subtitle.setObjectName("subtitleLabel")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        root.addLayout(header)

        # --- Onglets ---
        self.tabs = QTabWidget()
        self.camera_view = CameraView()
        self.settings_page = SettingsPage()
        self.gesture_page = GesturePage()

        self.tabs.addTab(self.camera_view, "Principal")
        self.tabs.addTab(self.settings_page, "Paramètres")
        self.tabs.addTab(self.gesture_page, "Gestes")

        self.settings_page.theme_changed.connect(self.apply_theme)
        self.settings_page.debug_toggled.connect(self.camera_view.set_debug_enabled)

        root.addWidget(self.tabs, stretch=1)
        self.setCentralWidget(central)

    def apply_theme(self, theme_name: str) -> None:
        self._theme = theme_name
        self.setStyleSheet(_build_stylesheet(theme_name))

    def closeEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        self.camera_view.shutdown()
        super().closeEvent(event)
