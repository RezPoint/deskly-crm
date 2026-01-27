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

    r = client.delete(f"/api/reminders/{reminder_id}")
    assert r.status_code == 204


def test_reminder_overdue_filter(client):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r = client.post("/api/reminders", json={"title": "Past", "due_at": past})
    assert r.status_code == 200
    past_id = r.json()["id"]

    r = client.get("/api/reminders", params={"overdue": "true"})
    assert r.status_code == 200
    assert any(rem["id"] == past_id for rem in r.json())


def test_reminder_entity_filters(client):
    due_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    r = client.post(
        "/api/reminders",
        json={"title": "Link", "due_at": due_at, "entity_type": "order", "entity_id": 123},
    )
    assert r.status_code == 200
    reminder_id = r.json()["id"]

    r = client.get("/api/reminders", params={"entity_type": "order", "entity_id": 123})
    assert r.status_code == 200
    assert any(rem["id"] == reminder_id for rem in r.json())


def test_ui_reminder_with_entity(client):
    r = client.post(
        "/api/reminders/ui",
        data={"title": "UI Link", "due_at": "2026-01-30T10:00", "entity_type": "client", "entity_id": "5"},
        follow_redirects=False,
    )
    assert r.status_code in {302, 303}


def test_ui_reminders_pagination(client):
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    for i in range(3):
        r = client.post("/api/reminders", json={"title": f"Page {i}", "due_at": due_at})
        assert r.status_code == 200

    r = client.get("/ui/reminders", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    assert "Page 1 / 2" in r.text
