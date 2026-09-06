"""
Point de montage entre Qt, le logging et la fenêtre principale.
"""
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QIcon

from core.constants import APP_NAME, FONT_FILES, FONTS_DIR, LOGO_PATH
from core.logger import setup_logger
from ui.main_window import MainWindow


def _load_brand_fonts() -> None:
    """Charge les polices Poppins/Inter de la charte graphique (spec :
    'utilise la charte graphique'). En cas d'échec, Qt retombe sur une
    police système équivalente — l'application reste utilisable."""
    for filename in FONT_FILES:
        path = FONTS_DIR / filename
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))


class Application:
    """Possède l'instance QApplication et la fenêtre principale."""

    def __init__(self):
        self.logger = setup_logger()
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName(APP_NAME)
        _load_brand_fonts()
        if LOGO_PATH.exists():
            self.qt_app.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.main_window = MainWindow()

    def run(self) -> int:
        self.logger.info("Démarrage de %s", APP_NAME)
        self.main_window.show()
        exit_code = self.qt_app.exec()
        self.logger.info("%s fermé (code %s)", APP_NAME, exit_code)
        return exit_code
