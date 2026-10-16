from app.repositories import flight_repository


def test_list_empty(client):
    assert client.get("/api/flights").json() == []


def test_flight_detail(client, db, sample_state):
    flight = flight_repository.upsert_active(db, sample_state)
    db.commit()

    resp = client.get(f"/api/flights/{flight.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["icao24"] == "39de57"
    assert body["callsign"] == "TVF431J"


def test_flight_detail_404(client):
    assert client.get("/api/flights/999999").status_code == 404
