from datetime import timedelta

from app.cache.aircraft_cache import AircraftCache
from app.schemas.aircraft import StateVector
from app.utils.time import utcnow


def _state(icao24, **kw):
    base = {"icao24": icao24}
    base.update(kw)
    return StateVector(**base)


def test_merge_keeps_recent_aircraft_missing_from_snapshot():
    cache = AircraftCache()
    a = _state("aaa111", latitude=1.0)
    b = _state("bbb222", latitude=2.0)
    cache.replace_all([a, b])

    # next poll only saw a; b should linger briefly instead of vanishing
    cache.merge([a], retain_seconds=60)

    assert {s.icao24 for s in cache.all()} == {"aaa111", "bbb222"}


def test_merge_drops_aircraft_past_retention():
    cache = AircraftCache()
    cache.replace_all([_state("ccc333", latitude=3.0)])
    cache._received_at["ccc333"] = utcnow() - timedelta(seconds=120)

    cache.merge([], retain_seconds=60)

    assert cache.all() == []


def test_merge_zero_retention_behaves_like_replace():
    cache = AircraftCache()
    cache.replace_all([_state("aaa111"), _state("bbb222")])

    cache.merge([_state("aaa111", latitude=5.0)], retain_seconds=0)

    states = cache.all()
    assert len(states) == 1
    assert states[0].latitude == 5.0


def test_merge_prefers_fresh_snapshot_over_retained():
    cache = AircraftCache()
    cache.replace_all([_state("aaa111", latitude=1.0)])

    cache.merge([_state("aaa111", latitude=9.0)], retain_seconds=60)

    assert cache.get("aaa111").latitude == 9.0
