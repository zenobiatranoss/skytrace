from app.cache.aircraft_cache import aircraft_cache
from app.services import position_service


def test_snapshot_maps_cache(db, sample_state):
    aircraft_cache.replace_all([sample_state])

    positions = position_service.snapshot()
    assert len(positions) == 1
    assert positions[0].icao24 == "39de57"
    assert positions[0].callsign == "TVF431J"


def test_bounds_filter(db, sample_state):
    aircraft_cache.replace_all([sample_state])

    inside = aircraft_cache.in_bounds((50.0, 5.0, 60.0, 20.0))
    outside = aircraft_cache.in_bounds((0.0, 0.0, 10.0, 10.0))
    assert len(inside) == 1
    assert outside == []


def test_stale_flag(db, sample_state):
    from app.utils.time import from_epoch

    # last contact far in the past should read as stale
    sample_state.last_contact = from_epoch(1)
    aircraft_cache.replace_all([sample_state])

    position = position_service.snapshot()[0]
    assert position.is_stale is True
    assert position.status == "stale"
