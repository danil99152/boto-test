import logging
import secrets
import string
from typing import Optional

from .db import get_connection

logger = logging.getLogger(__name__)

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 8


def _generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def create_short_url(original_url: str) -> str:
    """Создаёт запись в БД и возвращает уникальный код."""
    with get_connection() as conn:
        # Пытаемся несколько раз сгенерировать уникальный код, на случай коллизий
        for _ in range(5):
            code = _generate_code()
            try:
                conn.execute(
                    "INSERT INTO urls (code, original_url) VALUES (?, ?)",
                    (code, original_url),
                )
                logger.info("Создана короткая ссылка: %s -> %s", code, original_url)
                return code
            except Exception as exc:  # уникальный индекс мог сработать
                logger.warning("Коллизия кода %s: %s", code, exc)
        raise RuntimeError("Не удалось сгенерировать уникальный код короткой ссылки")


def get_original_url(code: str) -> Optional[str]:
    """Возвращает оригинальный URL по коду или None."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT original_url FROM urls WHERE code = ?",
            (code,),
        )
        row = cur.fetchone()
    if row:
        logger.info("Найден оригинальный URL для кода %s", code)
        return row[0]
    logger.info("Оригинальный URL для кода %s не найден", code)
    return None

