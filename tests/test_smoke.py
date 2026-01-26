def test_smoke_flow(client):
    # 1) create client
    r = client.post("/api/clients", json={"name": "Test Client", "phone": "+79990000000"})
    assert r.status_code == 200
    client_id = r.json()["id"]

    # 2) create order
    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "Landing page", "price": 15000, "status": "new"},
    )
    assert r.status_code == 200
    order_id = r.json()["id"]

    # 3) create payment
    r = client.post("/api/payments", json={"order_id": order_id, "amount": 8000})
    assert r.status_code == 200

    # 4) summary
    r = client.get(f"/api/orders/{order_id}/summary")
    assert r.status_code == 200
    data = r.json()
    assert round(data["price"], 2) == 15000.00
    assert round(data["paid_total"], 2) == 8000.00
    assert round(data["balance"], 2) == 7000.00

    # 5) export endpoints should respond
    r = client.get("/api/export/clients.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")

    r = client.get("/api/export/orders.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
