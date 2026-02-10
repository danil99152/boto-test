import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn

from .db import init_db
from .repository import create_short_url, get_original_url
from .schemas import ShortenRequest, ShortenResponse


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Инициализация приложения")
    init_db()
    yield
    logger.info("Остановка приложения")


app = FastAPI(title="Boto URL Shortener", lifespan=lifespan)


@app.post("/shorten", response_model=ShortenResponse)
async def shorten_url(payload: ShortenRequest) -> ShortenResponse:
    code = create_short_url(str(payload.url))
    base_url = os.getenv("BASE_URL")
    if base_url:
        short_url = f"{base_url.rstrip('/')}/{code}"
    else:
        # Для локальной разработки возвращаем просто относительный путь
        short_url = f"/{code}"
    logger.info("Отправлен короткий URL %s для %s", short_url, payload.url)
    return ShortenResponse(short_url=short_url)


@app.get("/{code}")
async def redirect(code: str):
    original_url = get_original_url(code)
    if not original_url:
        logger.warning("Код %s не найден", code)
        raise HTTPException(status_code=404, detail="Short URL not found")
    logger.info("Редирект с %s на %s", code, original_url)
    return RedirectResponse(url=original_url, status_code=307)


def run() -> None:
    """Точка входа для запуска через `python -m` или console_script."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )


if __name__ == "__main__":
    run()

