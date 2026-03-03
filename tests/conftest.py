import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models import User, Tenant
from app.core.security import hash_password

@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        db = TestingSessionLocal()
        try:
            tenant = Tenant(name="Default", slug="default")
            db.add(tenant)
            db.flush()
            user = User(email="owner@example.com", password_hash=hash_password("secret123"), role="owner")
            user.tenant_id = tenant.id
            db.add(user)
            db.commit()
        finally:
            db.close()

        # Login to get the cookie/token
        res = c.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "secret123"})
        if res.status_code == 200:
            c.headers["Authorization"] = f"Bearer {res.json()['access_token']}"
        yield c

    # clear overrides
    app.dependency_overrides.clear()


@pytest.fixture()
def anon_client(tmp_path):
    db_path = tmp_path / "test_anon.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # clear overrides
    app.dependency_overrides.clear()
