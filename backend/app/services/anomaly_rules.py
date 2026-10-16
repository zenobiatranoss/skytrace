"""Pure detectors that turn a state vector (+ a little recent movement) into
anomaly signals.

These are heuristics, not verdicts. Each one answers "is this worth a look?"
and nothing more - the message says what we saw, not what it means.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from app.schemas.aircraft import StateVector
from app.utils.coordinates import haversine_km


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


SEVERITY_RANK: dict[str, int] = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}

EMERGENCY_SQUAWKS: dict[str, str] = {
    "7500": "unlawful interference",
    "7600": "radio failure",
    "7700": "general emergency",
    "7777": "military intercept",
}

# thresholds - picked to be clearly abnormal, not merely unusual
RAPID_DESCENT_MS = -25.0  # ~ -4900 ft/min
RAPID_CLIMB_MS = 25.0
LOW_SPEED_MS = 40.0  # ~ 78 kt
# slow flight is only odd high up; light aircraft are slow down low by design
LOW_SPEED_MIN_ALT_M = 3000.0
# faster than any real aircraft - this is a data glitch or spoofing, not flight
JUMP_SPEED_MS = 500.0

LOITER_MIN_SAMPLES = 6
LOITER_MIN_SPAN_S = 300.0
LOITER_RADIUS_KM = 5.0
LOITER_MIN_RADIUS_KM = 0.3
LOITER_MIN_SPEED_MS = 40.0

_MS_PER_FPM = 0.00508
_MS_PER_KNOT = 0.514444


@dataclass
class Signal:
    kind: str
    severity: Severity
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class TrackSample:
    latitude: float
    longitude: float
    at: float  # epoch seconds, when we saw it
    altitude: float | None = None
    velocity: float | None = None
    position_at: float | None = None  # epoch seconds of the fix itself


def _fpm(ms: float) -> int:
    return round(ms / _MS_PER_FPM)


def check_squawk(state: StateVector) -> Signal | None:
    squawk = (state.squawk or "").strip()
    reason = EMERGENCY_SQUAWKS.get(squawk)
    if reason is None:
        return None
    return Signal(
        "emergency_squawk",
        Severity.CRITICAL,
        f"Squawking {squawk} - {reason}",
        {"squawk": squawk},
    )


def check_vertical_rate(state: StateVector) -> list[Signal]:
    rate = state.vertical_rate_ms
    if rate is None or state.on_ground:
        return []

    if rate <= RAPID_DESCENT_MS:
        return [
            Signal(
                "rapid_descent",
                Severity.HIGH,
                f"Descending at {abs(_fpm(rate)):,} ft/min",
                {"vertical_rate_ms": rate},
            )
        ]
    if rate >= RAPID_CLIMB_MS:
        return [
            Signal(
                "rapid_climb",
                Severity.MEDIUM,
                f"Climbing at {_fpm(rate):,} ft/min",
                {"vertical_rate_ms": rate},
            )
        ]
    return []


def check_low_speed(state: StateVector) -> Signal | None:
    velocity = state.velocity_ms
    if state.on_ground or velocity is None or velocity <= 0 or velocity >= LOW_SPEED_MS:
        return None
    # near the ground slow is normal; this is about being slow up high
    if state.altitude_m is not None and state.altitude_m < LOW_SPEED_MIN_ALT_M:
        return None

    knots = round(velocity / _MS_PER_KNOT)
    return Signal(
        "low_speed",
        Severity.MEDIUM,
        f"Low airspeed ({knots} kt)",
        {"velocity_ms": velocity},
    )


def _interval_seconds(state: StateVector, prev: TrackSample) -> float | None:
    """gap between two fixes. a lagging time_position means the true gap is
    larger than last_contact suggests, so take the more conservative value -
    otherwise a stale fix reads as a teleport."""
    candidates = [state.last_contact.timestamp() - prev.at]  # type: ignore[union-attr]
    if state.time_position is not None and prev.position_at is not None:
        candidates.append(state.time_position.timestamp() - prev.position_at)
    dt = max(candidates)
    return dt if dt > 0 else None


def check_position_jump(state: StateVector, prev: TrackSample | None) -> Signal | None:
    if prev is None or state.latitude is None or state.longitude is None:
        return None
    if state.last_contact is None:
        return None

    dt = _interval_seconds(state, prev)
    if dt is None:
        return None

    distance_km = haversine_km(
        prev.latitude, prev.longitude, state.latitude, state.longitude
    )
    implied_ms = (distance_km * 1000) / dt
    if implied_ms <= JUMP_SPEED_MS:
        return None

    return Signal(
        "position_jump",
        Severity.HIGH,
        f"Implied speed {round(implied_ms * 3.6):,} km/h between updates",
        {"implied_speed_ms": implied_ms, "distance_km": distance_km, "dt_seconds": dt},
    )


def check_loitering(
    history: list[TrackSample], on_ground: bool | None
) -> Signal | None:
    if on_ground or len(history) < LOITER_MIN_SAMPLES:
        return None

    span = history[-1].at - history[0].at
    if span < LOITER_MIN_SPAN_S:
        return None

    center_lat = sum(s.latitude for s in history) / len(history)
    center_lon = sum(s.longitude for s in history) / len(history)
    radius = max(
        haversine_km(center_lat, center_lon, s.latitude, s.longitude)
        for s in history
    )
    # a pinpoint means the feed is repeating one fix, not a circling aircraft
    if radius < LOITER_MIN_RADIUS_KM or radius > LOITER_RADIUS_KM:
        return None

    path_km = sum(
        haversine_km(history[i - 1].latitude, history[i - 1].longitude, history[i].latitude, history[i].longitude)
        for i in range(1, len(history))
    )
    # it has to actually travel - drifting across a small box is not loitering
    if path_km < 4 * radius:
        return None

    speeds = [s.velocity for s in history if s.velocity]
    mean_speed = sum(speeds) / len(speeds) if speeds else 0.0
    # parked or drifting doesn't count - it has to be flying in a tight area
    if mean_speed < LOITER_MIN_SPEED_MS:
        return None

    return Signal(
        "loitering",
        Severity.MEDIUM,
        f"Circling within {radius:.1f} km for {round(span / 60)} min",
        {"radius_km": radius, "span_seconds": span},
    )


def evaluate(
    state: StateVector,
    history: list[TrackSample],
    prev: TrackSample | None,
) -> list[Signal]:
    """run every detector for one aircraft. history includes the current
    sample; prev is the sample before it."""
    signals: list[Signal] = []

    for signal in (
        check_squawk(state),
        check_low_speed(state),
        check_position_jump(state, prev),
        check_loitering(history, state.on_ground),
    ):
        if signal is not None:
            signals.append(signal)

    signals.extend(check_vertical_rate(state))
    return signals


def highest_severity(signals: list[Signal]) -> Severity | None:
    if not signals:
        return None
    return max((s.severity for s in signals), key=lambda s: SEVERITY_RANK[s])
