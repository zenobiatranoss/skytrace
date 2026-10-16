from app.cache.aircraft_cache import aircraft_cache


def test_list_empty(client):
    resp = client.get("/api/aircraft")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_with_cached_state(client, sample_state):
    aircraft_cache.replace_all([sample_state])

    resp = client.get("/api/aircraft")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["icao24"] == "39de57"


def test_bounds_query(client, sample_state):
    aircraft_cache.replace_all([sample_state])

    hit = client.get("/api/aircraft", params={
        "lamin": 50, "lomin": 5, "lamax": 60, "lomax": 20,
    })
    miss = client.get("/api/aircraft", params={
        "lamin": 0, "lomin": 0, "lamax": 10, "lomax": 10,
    })
    assert len(hit.json()) == 1
    assert miss.json() == []


def test_detail_unknown_is_404(client):
    assert client.get("/api/aircraft/deadbe").status_code == 404


def test_detail_from_cache(client, sample_state, monkeypatch):
    from app.services import aircraft_service

    async def _no_route(db, icao24):
        return None

    monkeypatch.setattr(aircraft_service, "_route_info", _no_route)
    aircraft_cache.replace_all([sample_state])

    resp = client.get("/api/aircraft/39de57")
    assert resp.status_code == 200
    body = resp.json()
    assert body["identity"]["icao24"] == "39de57"
    assert body["position"]["callsign"] == "TVF431J"
    assert body["status"] == "airborne"
