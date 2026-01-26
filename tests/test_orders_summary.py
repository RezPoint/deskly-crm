from datetime import datetime, timezone


def test_orders_summary_filters(client):
    r = client.post("/api/clients", json={"name": "Summary Client"})
    client_id = r.json()["id"]

    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "A", "price": 100, "status": "new"},
    )
    order_id = r.json()["id"]

    client.post("/api/payments", json={"order_id": order_id, "amount": 30})

    r = client.get(f"/api/orders/summary/total?client_id={client_id}")
    assert r.status_code == 200
    data = r.json()
    assert round(data["price"], 2) == 100.00
    assert round(data["paid_total"], 2) == 30.00
    assert round(data["balance"], 2) == 70.00
