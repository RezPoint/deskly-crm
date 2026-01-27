def test_users_api_crud(client):
    # list users (owner already logged in)
    r = client.get("/api/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # create user
    r = client.post("/api/users", json={"email": "apiuser@example.com", "password": "secret123", "role": "viewer"})
    assert r.status_code == 200
    user_id = r.json()["id"]

    # reset password
    r = client.post(f"/api/users/{user_id}/reset-password", json={"password": "newsecret123"})
    assert r.status_code == 200

    # owner can change role
    r = client.patch(f"/api/users/{user_id}/role", json={"role": "admin"})
    assert r.status_code == 200
