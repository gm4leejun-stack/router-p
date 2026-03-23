import pytest
from fastapi.testclient import TestClient

from router_p.app import create_app
from router_p.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key="test-router-p-key")


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.api_key}"}
