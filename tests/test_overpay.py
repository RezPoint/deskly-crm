def test_payment_overpay_returns_409(client):
    r = client.post("/api/clients", json={"name": "A"})
    client_id = r.json()["id"]

    r = client.post("/api/orders", json={"client_id": client_id, "title": "Job", "price": 1000})
    order_id = r.json()["id"]

    r = client.post("/api/payments", json={"order_id": order_id, "amount": 800})
    assert r.status_code == 200

    r = client.post("/api/payments", json={"order_id": order_id, "amount": 300})
    assert r.status_code == 409