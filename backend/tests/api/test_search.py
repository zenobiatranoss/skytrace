from app.cache.aircraft_cache import aircraft_cache


def test_search_by_callsign(client, sample_state):
    aircraft_cache.replace_all([sample_state])

    resp = client.get("/api/search", params={"q": "TVF"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert any(r["id"] == "39de57" for r in results)


def test_search_empty_query_rejected(client):
    assert client.get("/api/search", params={"q": ""}).status_code == 422
