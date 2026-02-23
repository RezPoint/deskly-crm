def test_auth_me(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "owner@example.com"
    assert data["role"] == "owner"

def test_crud_client(client):
    # Create client
    res = client.post("/api/v1/clients", json={
        "name": "Test Client",
        "phone": "+123456",
        "notes": "Testing"
    })
    assert res.status_code == 200
    c_data = res.json()
    assert c_data["id"] > 0
    assert c_data["name"] == "Test Client"
    
    # List clients
    res2 = client.get("/api/v1/clients")
    assert res2.status_code == 200
    assert len(res2.json()) == 1
    
    # Validation error for duplicates ? Note: API may not enforce uniqueness globally, but it enforces it?
    # Actually, previous implementation didn't strictly forbid duplicated duplicate phones?
    
def test_crud_order_and_payment(client):
    # Create client first
    c_res = client.post("/api/v1/clients", json={"name": "Order Client"})
    c_id = c_res.json()["id"]
    
    # Create order
    res = client.post("/api/v1/orders", json={
        "client_id": c_id,
        "title": "Website Design",
        "price": "1000.00"
    })
    assert res.status_code == 200
    o_data = res.json()
    assert o_data["id"] > 0
    assert o_data["price"] == 1000.0
    o_id = o_data["id"]
    
    # Post payment
    p_res = client.post("/api/v1/payments", json={
        "order_id": o_id,
        "amount": "250.00"
    })
    assert p_res.status_code == 200
    
    # Summary
    s_res = client.get(f"/api/v1/orders/{o_id}/summary")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["balance"] == 750.0

def test_activity_log(client):
    # Check that previous creations logged activity. DB is fresh, so create something first.
    client.post("/api/v1/clients", json={"name": "Activity Gen Client", "notes": "Generate log"})
    
    res = client.get("/api/v1/activity")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    assert "client.created" in actions or "order.created" in actions

def test_reminders(client):
    res = client.post("/api/v1/reminders", json={
        "title": "Call client back",
        "due_at": "2030-01-01T10:00:00Z"
    })
    assert res.status_code == 200
    r_id = res.json()["id"]
    
    l_res = client.get("/api/v1/reminders")
    assert l_res.status_code == 200
    assert len(l_res.json()) >= 1
    
    # Patch reminder
    u_res = client.patch(f"/api/v1/reminders/{r_id}", json={"status": "done"})
    assert u_res.status_code == 200
    assert u_res.json()["status"] == "done"

def test_invites_and_users(client):
    res = client.post("/api/v1/invites", json={
        "email": "new.user@example.com",
        "role": "admin",
        "expires_in_days": 7
    })
    assert res.status_code == 200
    token = res.json()["token"]
    
    # Accept anonymously
    from app.main import app
    from fastapi.testclient import TestClient
    c2 = TestClient(app) # Anon client
    
    a_res = c2.post("/api/v1/invites/accept", json={
        "token": token,
        "password": "newpassword123"
    })
    assert a_res.status_code == 200
    assert a_res.json()["email"] == "new.user@example.com"
    
def test_export_clients(client):
    res = client.get("/api/v1/export/clients.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "client_id" in res.text

def test_export_orders(client):
    res = client.get("/api/v1/export/orders.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "order_id" in res.text
