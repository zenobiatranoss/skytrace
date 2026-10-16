from app.schemas.aircraft import StateVector
from app.services.anomaly_rules import (
    Severity,
    TrackSample,
    check_loitering,
    check_low_speed,
    check_position_jump,
    check_squawk,
    check_vertical_rate,
    evaluate,
)
from app.utils.time import from_epoch


def _state(**overrides) -> StateVector:
    base = {"icao24": "abc123", "on_ground": False}
    base.update(overrides)
    return StateVector(**base)


def test_emergency_squawk_is_critical():
    signal = check_squawk(_state(squawk="7700"))
    assert signal is not None
    assert signal.kind == "emergency_squawk"
    assert signal.severity == Severity.CRITICAL


def test_normal_squawk_is_ignored():
    assert check_squawk(_state(squawk="1200")) is None
    assert check_squawk(_state(squawk=None)) is None


def test_rapid_descent_and_climb():
    descent = check_vertical_rate(_state(vertical_rate_ms=-30.0))
    assert descent and descent[0].kind == "rapid_descent"
    assert descent[0].severity == Severity.HIGH

    climb = check_vertical_rate(_state(vertical_rate_ms=25.0))
    assert climb and climb[0].kind == "rapid_climb"

    assert check_vertical_rate(_state(vertical_rate_ms=-5.0)) == []


def test_vertical_rate_ignored_on_ground():
    assert check_vertical_rate(_state(vertical_rate_ms=-40.0, on_ground=True)) == []


def test_low_speed_flags_slow_high_aircraft():
    signal = check_low_speed(_state(velocity_ms=30.0, altitude_m=5000.0))
    assert signal is not None
    assert signal.kind == "low_speed"

    # slow down low is normal for light aircraft, so it's ignored
    assert check_low_speed(_state(velocity_ms=30.0, altitude_m=1500.0)) is None
    # normal cruise speed is fine
    assert check_low_speed(_state(velocity_ms=220.0, altitude_m=10000.0)) is None


def test_position_jump_flags_impossible_speed():
    prev = TrackSample(latitude=0.0, longitude=0.0, at=1000.0)
    state = _state(latitude=1.0, longitude=1.0)
    state.last_contact = from_epoch(1010)  # ~157km in 10s

    signal = check_position_jump(state, prev)
    assert signal is not None
    assert signal.kind == "position_jump"


def test_position_jump_allows_normal_movement():
    prev = TrackSample(latitude=0.0, longitude=0.0, at=1000.0)
    state = _state(latitude=0.02, longitude=0.02)  # ~3km in 60s
    state.last_contact = from_epoch(1060)

    assert check_position_jump(state, prev) is None


def test_position_jump_uses_the_longer_interval():
    # last_contact implies 10s but the position fix is a minute old, so the
    # gap is really ~60s and the move is ordinary - not a teleport.
    prev = TrackSample(latitude=0.0, longitude=0.0, at=1000.0, position_at=1000.0)
    state = _state(latitude=0.072, longitude=0.0)  # ~8km
    state.last_contact = from_epoch(1010)
    state.time_position = from_epoch(1060)

    assert check_position_jump(state, prev) is None


def _circle_since(start: float, count: int, step: float = 60.0) -> list[TrackSample]:
    samples = []
    for i in range(count):
        # tight offsets, well inside the radius
        dlat = 0.005 if i % 2 else -0.005
        dlon = 0.005 if i % 3 else -0.005
        samples.append(
            TrackSample(
                latitude=50.0 + dlat,
                longitude=10.0 + dlon,
                at=start + i * step,
                velocity=100.0,
            )
        )
    return samples


def test_loitering_flags_tight_circling():
    history = _circle_since(0.0, 6)
    signal = check_loitering(history, on_ground=False)
    assert signal is not None
    assert signal.kind == "loitering"


def test_loitering_needs_enough_time():
    history = _circle_since(0.0, 6, step=10.0)  # only 50s span
    assert check_loitering(history, on_ground=False) is None


def test_loitering_ignores_wide_drift():
    history = [
        TrackSample(latitude=50.0 + i, longitude=10.0, at=i * 60.0, velocity=100.0)
        for i in range(6)
    ]
    assert check_loitering(history, on_ground=False) is None


def test_loitering_ignores_a_frozen_fix():
    # the feed re-serving one position is a pinpoint, not a circling aircraft
    history = [
        TrackSample(latitude=50.0, longitude=10.0, at=i * 60.0, velocity=100.0)
        for i in range(6)
    ]
    assert check_loitering(history, on_ground=False) is None


def test_evaluate_collects_multiple_signals():
    state = _state(squawk="7700", vertical_rate_ms=-30.0)
    signals = evaluate(state, [], None)
    kinds = {s.kind for s in signals}
    assert kinds == {"emergency_squawk", "rapid_descent"}
