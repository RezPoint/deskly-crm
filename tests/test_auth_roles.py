from sqlalchemy import select

from app.models import User, Tenant
from app.security import hash_password


def test_viewer_cannot_write(client):
    db = client.app.state.SessionLocal()
    try:
        tenant = db.execute(select(Tenant)).scalar_one()
        viewer = User(email="viewer@example.com", password_hash=hash_password("viewer123"), role="viewer")
        viewer.tenant_id = tenant.id
        db.add(viewer)
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/login", json={"email": "viewer@example.com", "password": "viewer123"})
    assert r.status_code == 200

    r = client.post("/api/clients", json={"name": "Nope"})
    assert r.status_code == 403


def test_admin_can_manage_users_but_not_roles(client):
    db = client.app.state.SessionLocal()
    try:
        tenant = db.execute(select(Tenant)).scalar_one()
        admin = User(email="admin@example.com", password_hash=hash_password("admin123"), role="admin")
        admin.tenant_id = tenant.id
        db.add(admin)
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert r.status_code == 200

    r = client.post("/api/users", json={"email": "new@example.com", "password": "newpass123", "role": "viewer"})
    assert r.status_code == 200

    r = client.patch("/api/users/1/role", json={"role": "admin"})
    assert r.status_code == 403
