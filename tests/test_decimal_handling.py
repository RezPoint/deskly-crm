def test_summary_with_fractional_values(client):
    r = client.post("/api/clients", json={"name": "Decimal Client"})
    client_id = r.json()["id"]

    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "Precision Job", "price": 10.01},
    )
    order_id = r.json()["id"]

    r = client.post("/api/payments", json={"order_id": order_id, "amount": 0.02})
    assert r.status_code == 200

    r = client.get(f"/api/orders/{order_id}/summary")
    assert r.status_code == 200
    data = r.json()
    assert round(data["paid_total"], 2) == 0.02
    assert round(data["balance"], 2) == 9.99


def test_overpay_with_fractional_values_returns_409(client):
    r = client.post("/api/clients", json={"name": "Overpay Client"})
    client_id = r.json()["id"]

    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "Small Job", "price": 10.01},
    )
    order_id = r.json()["id"]

    r = client.post("/api/payments", json={"order_id": order_id, "amount": 10.00})
    assert r.status_code == 200

    r = client.post("/api/payments", json={"order_id": order_id, "amount": 0.02})
    assert r.status_code == 409
