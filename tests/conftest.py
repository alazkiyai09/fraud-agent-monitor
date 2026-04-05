import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.rate_limit import rate_limiter


@pytest.fixture()
def client() -> TestClient:
    get_settings.cache_clear()
    rate_limiter.clear()
    with TestClient(app) as test_client:
        yield test_client
    rate_limiter.clear()
    get_settings.cache_clear()


@pytest.fixture()
def sample_transactions() -> list[dict]:
    data = json.loads(Path("data/sample_transactions.json").read_text(encoding="utf-8"))
    return data
