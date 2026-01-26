from datetime import datetime, timezone, timedelta


def test_list_orders_filters_by_date(client):
    r = client.post("/api/clients", json={"name": "Date Client"})
    client_id = r.json()["id"]

    r = client.post("/api/orders", json={"client_id": client_id, "title": "Old", "price": 10})
    old_id = r.json()["id"]

    r = client.post("/api/orders", json={"client_id": client_id, "title": "New", "price": 20})
    new_id = r.json()["id"]

    from app.models import Order

    with client.app.state.SessionLocal() as db:
        old_order = db.get(Order, old_id)
        new_order = db.get(Order, new_id)
        old_order.created_at = datetime.now(timezone.utc) - timedelta(days=10)
        new_order.created_at = datetime.now(timezone.utc)
        db.commit()

    date_from = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    r = client.get(f"/api/orders?date_from={date_from}")
    assert r.status_code == 200
    titles = {o["title"] for o in r.json()}
    assert "Old" not in titles
    assert "New" in titles
