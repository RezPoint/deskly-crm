def test_delete_order_cascades_payments(client):
    r = client.post("/api/clients", json={"name": "Del Client"})
    client_id = r.json()["id"]

    r = client.post("/api/orders", json={"client_id": client_id, "title": "Del Order", "price": 100})
    order_id = r.json()["id"]

    r = client.post("/api/payments", json={"order_id": order_id, "amount": 40})
    payment_id = r.json()["id"]

    r = client.get(f"/api/payments/by-order/{order_id}")
    assert r.status_code == 200
    assert any(p["id"] == payment_id for p in r.json())

    r = client.delete(f"/api/orders/{order_id}")
    assert r.status_code == 204

    r = client.get(f"/api/orders/{order_id}")
    assert r.status_code == 404

    r = client.get(f"/api/payments/by-order/{order_id}")
    assert r.status_code == 404


def test_delete_client_cascades_orders(client):
    r = client.post("/api/clients", json={"name": "Del Client 2"})
    client_id = r.json()["id"]

    r = client.post("/api/orders", json={"client_id": client_id, "title": "Del Order 2", "price": 50})
    order_id = r.json()["id"]

    r = client.delete(f"/api/clients/{client_id}")
    assert r.status_code == 204

    r = client.get(f"/api/clients/{client_id}")
    assert r.status_code == 404

    r = client.get(f"/api/orders/{order_id}")
    assert r.status_code == 404
