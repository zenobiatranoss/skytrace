def test_airport_missing_dataset_is_404(client):
    # no csv configured in tests, so an unknown code honestly comes back empty
    assert client.get("/api/airports/XXXX").status_code == 404


def test_arrivals_empty(client):
    resp = client.get("/api/airports/EDDF/arrivals")
    assert resp.status_code == 200
    assert resp.json() == []
