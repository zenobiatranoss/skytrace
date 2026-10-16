import pytest

from app.core.config import settings
from app.models.anomaly import Anomaly
from app.repositories import anomaly_repository
from app.schemas.aircraft import StateVector
from app.services import anomaly_service
from app.utils.time import utcnow


@pytest.fixture(autouse=True)
def _clean(db):
    # module-level state is shared, so reset it and the table each time
    anomaly_service._history.clear()
    anomaly_service._active_views = []
    db.query(Anomaly).delete()
    db.commit()
    yield
    anomaly_service._history.clear()
    anomaly_service._active_views = []


def _squawking(icao24: str = "abc123") -> StateVector:
    return StateVector(
        icao24=icao24,
        squawk="7700",
        latitude=1.0,
        longitude=2.0,
        on_ground=False,
    )


def test_detect_flags_emergency_squawk():
    result = anomaly_service.detect([_squawking()])
    assert "abc123" in result
    assert "emergency_squawk" in {s.kind for s in result["abc123"]}


def test_evaluate_cycle_persists_and_dedupes(db):
    anomaly_service.evaluate_cycle([_squawking()])
    anomaly_service.evaluate_cycle([_squawking()])

    rows = [r for r in anomaly_repository.for_aircraft(db, "abc123") if r.active]
    assert len(rows) == 1
    assert rows[0].kind == "emergency_squawk"
    assert rows[0].severity == "critical"


def test_anomaly_resolves_once_condition_clears(db, monkeypatch):
    # with no hold time, a clean next cycle closes the old flag
    monkeypatch.setattr(settings, "anomaly_hold_seconds", 0)

    anomaly_service.evaluate_cycle([_squawking()])
    clean = StateVector(icao24="def456", latitude=1.0, longitude=2.0, on_ground=False)
    anomaly_service.evaluate_cycle([clean])

    assert anomaly_repository.get_active(db, "abc123", "emergency_squawk") is None


def test_empty_cycle_does_not_close_open_anomalies(db):
    anomaly_service.evaluate_cycle([_squawking()])
    # a provider hiccup returning nothing shouldn't wipe the feed
    anomaly_service.evaluate_cycle([])
    assert anomaly_repository.get_active(db, "abc123", "emergency_squawk") is not None


def test_reset_closes_previous_run(db):
    anomaly_service.evaluate_cycle([_squawking()])
    closed = anomaly_service.reset(db)
    assert closed == 1
    assert anomaly_repository.list_active(db) == []


def test_detect_does_not_loiter_on_a_repeated_fix():
    # the same position every cycle must not accumulate into a loiter
    result: dict = {}
    for _ in range(8):
        state = StateVector(
            icao24="loit1",
            latitude=50.0,
            longitude=10.0,
            on_ground=False,
            velocity_ms=100.0,
            last_contact=utcnow(),
        )
        result = anomaly_service.detect([state])

    kinds = {s.kind for s in result.get("loit1", [])}
    assert "loitering" not in kinds
