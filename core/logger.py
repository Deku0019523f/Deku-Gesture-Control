"""
Configuration centralisée du logging (spec section 23).

Usage :
    from core.logger import setup_logger
    logger = setup_logger()
    logger.info("message")

Règle : ne jamais logger d'informations sensibles (frames vidéo, images,
coordonnées précises d'écran, etc.).
"""
import logging
import logging.handlers

from core.constants import LOGS_DIR

_configured = False


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure et retourne le logger racine de l'application.

    Peut être appelée plusieurs fois sans effet de bord : la configuration
    n'est appliquée qu'une seule fois.
    """
    global _configured
    logger = logging.getLogger("deku")

    if _configured:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / "deku.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("Impossible de créer le fichier de log, console uniquement.")

    logger.propagate = False
    _configured = True
    return logger
