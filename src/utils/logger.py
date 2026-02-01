import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from settings import settings

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("faker").setLevel(logging.WARNING)


def setup_logging() -> None:
    """Настройка логирования. Вызывать при старте приложения."""
    LOG_DIR.mkdir(exist_ok=True)

    level = settings.LOG_LEVEL
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)
    root.addHandler(console)
    root.addHandler(file_handler)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logging.info(">>> LOGGING CONFIGURED (level=%s) <<<", level)