import pytest
import database.connection as conn_module
from database.connection import setup_database
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def test_db(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(conn_module, "DB_FILE", db_path)
    setup_database()


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Crée un utilisateur test et retourne le header Authorization JWT."""
    client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = r.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
