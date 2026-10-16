import pytest

from app.models.anomaly import Anomaly
from app.repositories import anomaly_repository
from app.utils.time import utcnow


@pytest.fixture(autouse=True)
def _clean(db):
    db.query(Anomaly).delete()
    db.commit()
    yield


def _add(db, icao24="abc123", kind="emergency_squawk", severity="critical"):
    anomaly_repository.upsert_active(
        db,
        icao24=icao24,
        kind=kind,
        severity=severity,
        message=f"{kind} for {icao24}",
        now=utcnow(),
    )
    db.commit()


def test_list_empty(client):
    body = client.get("/api/anomalies").json()
    assert body == {"count": 0, "items": []}


def test_list_returns_active(client, db):
    _add(db)
    body = client.get("/api/anomalies").json()
    assert body["count"] == 1
    assert body["items"][0]["icao24"] == "abc123"
    assert body["items"][0]["active"] is True


def test_filter_by_severity(client, db):
    _add(db, icao24="aaa111", severity="critical")
    _add(db, icao24="bbb222", kind="loitering", severity="medium")

    body = client.get("/api/anomalies", params={"severity": "medium"}).json()
    assert body["count"] == 1
    assert body["items"][0]["icao24"] == "bbb222"


def test_filter_by_kind(client, db):
    _add(db, icao24="aaa111", kind="emergency_squawk")
    _add(db, icao24="bbb222", kind="rapid_descent", severity="high")

    body = client.get("/api/anomalies", params={"kind": "rapid_descent"}).json()
    assert body["count"] == 1
    assert body["items"][0]["kind"] == "rapid_descent"


def test_count_is_the_total_not_the_page(client, db):
    for i in range(3):
        _add(db, icao24=f"aaa00{i}", kind="loitering", severity="medium")

    body = client.get("/api/anomalies", params={"limit": 2}).json()
    assert body["count"] == 3
    assert len(body["items"]) == 2


def test_aircraft_anomalies(client, db):
    _add(db, icao24="aaa111")
    _add(db, icao24="bbb222", kind="loitering", severity="medium")

    body = client.get("/api/anomalies/aaa111").json()
    assert len(body) == 1
    assert body[0]["icao24"] == "aaa111"


def test_aircraft_anomalies_unknown_is_empty(client):
    assert client.get("/api/anomalies/zzzzzz").json() == []
