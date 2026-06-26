import os

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    db = tmp_path / "test.db"
    application = create_app({"TESTING": True, "DATABASE_PATH": str(db), "API_KEY": "test-key"})
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth():
    return {"X-API-Key": "test-key"}
