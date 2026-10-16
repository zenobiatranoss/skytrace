from enum import StrEnum


class FlightStatus(StrEnum):
    UNKNOWN = "unknown"
    ON_GROUND = "on_ground"
    AIRBORNE = "airborne"
    STALE = "stale"


def derive_status(
    on_ground: bool | None,
    last_contact_seconds: float | None,
    stale_after: int,
) -> FlightStatus:
    """coarse status from what we actually know, no guessing"""
    if last_contact_seconds is not None and last_contact_seconds > stale_after:
        return FlightStatus.STALE
    if on_ground is None:
        return FlightStatus.UNKNOWN
    return FlightStatus.ON_GROUND if on_ground else FlightStatus.AIRBORNE
