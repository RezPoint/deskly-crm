from datetime import datetime, timezone, timedelta


def test_export_orders_filters_by_client_and_date(client):
    r = client.post("/api/clients", json={"name": "Export Client"})
    client_id = r.json()["id"]

    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "Old", "price": 10, "status": "new"},
    )
    old_id = r.json()["id"]

    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "New", "price": 20, "status": "new"},
    )
    new_id = r.json()["id"]

    # Directly patch created_at timestamps for predictable filtering
    from app.models import Order

    with client.app.state.SessionLocal() as db:
        old_order = db.get(Order, old_id)
        new_order = db.get(Order, new_id)
        old_order.created_at = datetime.now(timezone.utc) - timedelta(days=10)
        new_order.created_at = datetime.now(timezone.utc)
        db.commit()

    date_from = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    r = client.get(f"/api/export/orders.csv?client_id={client_id}&date_from={date_from}")
    assert r.status_code == 200
    body = r.text
    assert "Old" not in body
    assert "New" in body
