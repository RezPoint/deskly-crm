def test_extras_increase_total_and_allow_payment(client):
    # create client
    r = client.post("/api/clients", json={"name": "T", "phone": "+79990000001"})
    assert r.status_code == 200
    client_id = r.json()["id"]

    # create order base price 15000
    r = client.post("/api/orders", json={"client_id": client_id, "title": "Landing", "price": 15000, "status": "new"})
    assert r.status_code == 200
    order_id = r.json()["id"]

    # pay 8000
    r = client.post("/api/payments", json={"order_id": order_id, "amount": 8000})
    assert r.status_code == 200

    # add extra 3000
    r = client.post(f"/api/orders/{order_id}/extras", json={"amount": 3000, "reason": "Revisions"})
    assert r.status_code == 200

    # now total price = 18000, balance = 10000
    r = client.get(f"/api/orders/{order_id}/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_price"] == "18000.00"
    assert data["balance"] == "10000.00"

    # pay remaining 10000 should be ok
    r = client.post("/api/payments", json={"order_id": order_id, "amount": 10000})
    assert r.status_code == 200