def test_ui_orders_flow(client):
    r = client.post(
        "/api/clients",
        json={"name": "UI Client", "phone": "+100000000"},
    )
    client_id = r.json()["id"]

    r = client.post(
        "/api/orders",
        json={"client_id": client_id, "title": "UI Job", "price": 150},
    )
    order_id = r.json()["id"]

    r = client.get("/ui/orders")
    assert r.status_code == 200
    assert "UI Job" in r.text

    r = client.get(f"/ui/orders/{order_id}")
    assert r.status_code == 200
    assert "UI Job" in r.text
    assert "UI Client" in r.text


def test_ui_clients_duplicate_shows_error(client):
    r = client.post("/api/clients", json={"name": "Dup", "phone": "+999"})
    assert r.status_code == 200

    r = client.post(
        "/ui/clients",
        data={"name": "Dup2", "phone": "+999"},
    )
    assert r.status_code == 409
    assert "Client with same phone/telegram already exists" in r.text
