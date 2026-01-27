def test_activity_log_records_actions(client):
    r = client.post("/api/clients", json={"name": "Log Client"})
    assert r.status_code == 200
    client_id = r.json()["id"]

    r = client.get("/api/activity")
    assert r.status_code == 200
    logs = r.json()
    assert logs
    assert logs[0]["action"] in {"client.created", "client.deleted", "order.created", "payment.created"}
    # ensure at least one client.created for this client id appears
    assert any(l["action"] == "client.created" and l["entity_id"] == client_id for l in logs)


def test_activity_log_filters(client):
    r = client.post("/api/clients", json={"name": "Filter Client"})
    assert r.status_code == 200
    client_id = r.json()["id"]

    r = client.get("/api/activity", params={"entity_type": "client", "action": "client.created"})
    assert r.status_code == 200
    assert any(l["entity_id"] == client_id for l in r.json())
