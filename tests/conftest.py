import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.models import User
from app.security import hash_password


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(f"sqlite:///{db_path}")

    with TestClient(app) as c:
        db = app.state.SessionLocal()
        try:
            user = User(email="owner@example.com", password_hash=hash_password("secret123"), role="owner")
            db.add(user)
            db.commit()
        finally:
            db.close()

        c.post("/api/auth/login", json={"email": "owner@example.com", "password": "secret123"})
        yield c


@pytest.fixture()
def anon_client(tmp_path):
    db_path = tmp_path / "test_anon.db"
    app = create_app(f"sqlite:///{db_path}")
    with TestClient(app) as c:
        yield c
