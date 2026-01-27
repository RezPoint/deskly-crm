def test_client_phone_validation(client):
    r = client.post("/api/clients", json={"name": "Bad Phone", "phone": "abc"})
    assert r.status_code == 422


def test_client_telegram_validation_and_normalization(client):
    r = client.post("/api/clients", json={"name": "Bad Tg", "telegram": "???"})
    assert r.status_code == 422

    r = client.post("/api/clients", json={"name": "Good Tg", "telegram": "my_handle"})
    assert r.status_code == 200
    assert r.json()["telegram"] == "@my_handle"
