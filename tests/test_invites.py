def test_invite_flow(client):
    r = client.post(
        "/api/invites",
        json={"email": "invitee@example.com", "role": "viewer", "expires_in_days": 7},
    )
    assert r.status_code == 200
    token = r.json()["token"]
    assert token

    r = client.post("/api/invites/accept", json={"token": token, "password": "secret123"})
    assert r.status_code == 200

    r = client.post("/api/auth/login", json={"email": "invitee@example.com", "password": "secret123"})
    assert r.status_code == 200


def test_invite_invalid_token(client):
    r = client.post("/api/invites/accept", json={"token": "nope", "password": "secret123"})
    assert r.status_code == 404
