def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert "service" in data
    assert "version" in data
    assert data["uptime_seconds"] >= 0
