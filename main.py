"""
Deku Gesture Control — point d'entrée.

Phase 1 : lance l'application, affiche l'aperçu webcam avec FPS et un
bouton Start/Stop. Aucune reconnaissance de gestes pour l'instant.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.application import Application  # noqa: E402


def main() -> int:
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
