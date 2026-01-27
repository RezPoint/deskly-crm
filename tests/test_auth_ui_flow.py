from sqlalchemy import select

from app.models import User, Tenant
from app.security import hash_password


def test_setup_then_login_flow(anon_client):
    r = anon_client.get("/setup")
    assert r.status_code == 200

    r = anon_client.post("/setup", data={"email": "owner@site.com", "password": "secret123"}, follow_redirects=False)
    assert r.status_code in {302, 303}

    r = anon_client.get("/login")
    assert r.status_code == 200

    r = anon_client.post("/login", data={"email": "owner@site.com", "password": "secret123"}, follow_redirects=False)
    assert r.status_code in {302, 303}

    r = anon_client.get("/ui/clients")
    assert r.status_code == 200


def test_login_redirects_to_setup_when_no_users(anon_client):
    r = anon_client.get("/login", follow_redirects=False)
    assert r.status_code in {302, 303}
    assert r.headers["location"] == "/setup"


def test_anon_redirected_to_login(client, anon_client):
    r = anon_client.get("/ui/orders", follow_redirects=False)
    assert r.status_code in {302, 303}
    assert r.headers["location"] in {"/login", "/setup"}


def test_viewer_restrictions_ui(client):
    db = client.app.state.SessionLocal()
    try:
        tenant = db.execute(select(Tenant)).scalar_one()
        viewer = User(email="viewer2@example.com", password_hash=hash_password("viewer123"), role="viewer")
        viewer.tenant_id = tenant.id
        db.add(viewer)
        db.commit()
    finally:
        db.close()

    viewer_client = client
    viewer_client.post("/api/auth/login", json={"email": "viewer2@example.com", "password": "viewer123"})

    r = viewer_client.get("/ui/clients")
    assert r.status_code == 200

    r = viewer_client.post("/ui/clients", data={"name": "Nope"})
    assert r.status_code == 403

    r = viewer_client.get("/ui/users", follow_redirects=False)
    assert r.status_code in {302, 303}
    assert r.headers["location"] == "/ui/clients"


def test_setup_hidden_after_user_created(anon_client):
    anon_client.post("/setup", data={"email": "owner@site.com", "password": "secret123"}, follow_redirects=False)
    r = anon_client.get("/setup", follow_redirects=False)
    assert r.status_code in {302, 303}
    assert r.headers["location"] == "/login"


def test_activity_ui_filters_and_validation(client):
    r = client.get("/ui/activity", params={"entity_type": "client"})
    assert r.status_code == 200

    r = client.get("/ui/activity", params={"date_from": "2026-01-02", "date_to": "2026-01-01"})
    assert r.status_code == 422
