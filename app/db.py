import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


DB_PATH = Path(os.getenv("SHORTENER_DB_PATH", "shortener.db"))


def init_db() -> None:
    """Инициализация схемы БД (если ещё не создана)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    logger.info("База данных инициализирована по пути %s", DB_PATH)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Контекстный менеджер для работы с соединением sqlite."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Ошибка при работе с БД, выполнен rollback")
        raise
    finally:
        conn.close()

