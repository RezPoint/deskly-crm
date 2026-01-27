def _csv_file(content: str):
    return {"file": ("data.csv", content.encode("utf-8"), "text/csv")}


def test_import_clients_csv(client):
    csv = "name,phone,telegram,notes\nAlice,+123,,note\nBob,,@bobby,\n"
    r = client.post("/api/import/clients", files=_csv_file(csv))
    assert r.status_code == 200
    assert r.json()["created"] == 2


def test_import_orders_csv(client):
    r = client.post("/api/clients", json={"name": "CSV Client"})
    assert r.status_code == 200
    client_id = r.json()["id"]
    csv = f"client_id,title,price,status,comment\n{client_id},Order A,100,new,\n"
    r = client.post("/api/import/orders", files=_csv_file(csv))
    assert r.status_code == 200
    assert r.json()["created"] == 1


def test_import_orders_invalid_client(client):
    csv = "client_id,title,price,status\n999,Order X,10,new\n"
    r = client.post("/api/import/orders", files=_csv_file(csv))
    assert r.status_code == 422
