from app.models import User
from app.security import hash_password


def test_viewer_cannot_write(client):
    db = client.app.state.SessionLocal()
    try:
        viewer = User(email="viewer@example.com", password_hash=hash_password("viewer123"), role="viewer")
        db.add(viewer)
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/login", json={"email": "viewer@example.com", "password": "viewer123"})
    assert r.status_code == 200

    r = client.post("/api/clients", json={"name": "Nope"})
    assert r.status_code == 403
