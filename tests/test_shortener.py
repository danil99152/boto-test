import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Гарантируем, что корень проекта (с пакетом app) в sys.path,
# независимо от того, откуда запущен pytest.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["SHORTENER_DB_PATH"] = os.path.join(tempfile.gettempdir(), "shortener_test.db")
os.environ["BASE_URL"] = "http://0.0.0.0:8000"

from app.main import app  # noqa: E402
from app.db import init_db  # noqa: E402


@pytest.fixture(autouse=True)
def _init_db():
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_shorten_and_redirect(client: TestClient):
    resp = client.post("/shorten", json={"url": "http://0.0.0.0:8000"})
    assert resp.status_code == 200
    data = resp.json()
    assert "short_url" in data
    short_url = data["short_url"]
    code = short_url.rsplit("/", 1)[-1]

    redirect_resp = client.get(f"/{code}", follow_redirects=False)
    assert redirect_resp.status_code == 307
    # Pydantic HttpUrl нормализует URL и может добавлять завершающий слеш,
    # поэтому сравниваем URL без завершающего слеша.
    assert redirect_resp.headers["location"].rstrip("/") == "http://0.0.0.0:8000"


def test_redirect_not_found(client: TestClient):
    resp = client.get("/nonexistent", follow_redirects=False)
    assert resp.status_code == 404


def test_shorten_invalid_url(client: TestClient):
    # Невалидный URL должен отбрасываться валидацией Pydantic/FastAPI
    resp = client.post("/shorten", json={"url": "not-a-url"})
    assert resp.status_code == 422


def test_multiple_shortens_for_same_url_produce_valid_codes(client: TestClient):
    # Проверяем, что несколько вызовов для одного и того же URL создают рабочие коды
    codes = set()
    for _ in range(3):
        resp = client.post("/shorten", json={"url": "http://0.0.0.0:8000"})
        assert resp.status_code == 200
        data = resp.json()
        code = data["short_url"].rsplit("/", 1)[-1]
        assert code  # непустой код
        assert len(code) == 8
        codes.add(code)

        redirect_resp = client.get(f"/{code}", follow_redirects=False)
        assert redirect_resp.status_code == 307
        assert redirect_resp.headers["location"].rstrip("/") == "http://0.0.0.0:8000"

    # В текущей реализации каждый раз создаётся новая запись, поэтому коды могут отличаться.
    # Это не критично для задания, но фиксируем, что как минимум один код существует.
    assert len(codes) >= 1

