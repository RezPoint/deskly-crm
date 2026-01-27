from datetime import datetime, timezone, timedelta


def test_reminder_crud(client):
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = client.post("/api/reminders", json={"title": "Pay invoice", "due_at": due_at})
    assert r.status_code == 200
    reminder_id = r.json()["id"]

    r = client.get("/api/reminders")
    assert r.status_code == 200
    assert any(rem["id"] == reminder_id for rem in r.json())

    r = client.patch(f"/api/reminders/{reminder_id}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"
