"""
Point de montage entre Qt, le logging et la fenêtre principale.
"""
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from core.constants import APP_NAME, LOGO_PATH
from core.logger import setup_logger
from ui.main_window import MainWindow


class Application:
    """Possède l'instance QApplication et la fenêtre principale."""

    def __init__(self):
        self.logger = setup_logger()
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName(APP_NAME)
        if LOGO_PATH.exists():
            self.qt_app.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.main_window = MainWindow()

    def run(self) -> int:
        self.logger.info("Démarrage de %s", APP_NAME)
        self.main_window.show()
        exit_code = self.qt_app.exec()
        self.logger.info("%s fermé (code %s)", APP_NAME, exit_code)
        return exit_code
