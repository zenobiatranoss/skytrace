from datetime import UTC, datetime

from app.schemas.aircraft import StateVector

# fields we're happy to borrow from a lower-priority source when the primary
# one left them blank. anything identity-ish is left alone on purpose.
FILL_FIELDS = (
    "callsign",
    "origin_country",
    "latitude",
    "longitude",
    "altitude_m",
    "geo_altitude_m",
    "velocity_ms",
    "heading",
    "vertical_rate_ms",
    "on_ground",
    "squawk",
    "position_source",
    "time_position",
    "last_contact",
)

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _recency(state: StateVector) -> datetime:
    return state.time_position or state.last_contact or _EPOCH


def merge_states(sources: list[list[StateVector]]) -> list[StateVector]:
    """combine per-source snapshots into one list keyed by icao24.

    ``sources`` is in priority order. per aircraft we start from the most
    recent fix (ties go to the earlier source) and then fill in whatever is
    still missing from the rest, so a fast empty-ish feed can't blank out
    fields a slower one already knows.
    """
    grouped: dict[str, list[StateVector]] = {}
    for states in sources:
        for state in states:
            grouped.setdefault(state.icao24, []).append(state)

    merged: list[StateVector] = []
    for records in grouped.values():
        # stable sort: equal recency keeps source order, so the higher
        # priority record stays first
        ordered = sorted(records, key=_recency, reverse=True)
        base = ordered[0].model_copy()
        for other in ordered[1:]:
            for field in FILL_FIELDS:
                if getattr(base, field) is None:
                    value = getattr(other, field)
                    if value is not None:
                        setattr(base, field, value)
        merged.append(base)
    return merged
