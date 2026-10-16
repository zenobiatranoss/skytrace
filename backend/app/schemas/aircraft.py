from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class StateVector(BaseModel):
    """normalized live position. every provider gets mapped into this shape
    so the rest of the app only deals with one thing."""

    icao24: str
    callsign: str | None = None
    origin_country: str | None = None

    latitude: float | None = None
    longitude: float | None = None
    # barometric altitude, meters. geo altitude kept separate when present
    altitude_m: float | None = None
    geo_altitude_m: float | None = None

    velocity_ms: float | None = None
    heading: float | None = None
    vertical_rate_ms: float | None = None
    on_ground: bool | None = None

    squawk: str | None = None
    position_source: int | None = None

    time_position: datetime | None = None
    last_contact: datetime | None = None


class AircraftPosition(BaseModel):
    """flat shape used by the map and aircraft list. identity + last vector"""

    icao24: str
    callsign: str | None = None
    registration: str | None = None
    type_code: str | None = None

    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    velocity_ms: float | None = None
    heading: float | None = None
    vertical_rate_ms: float | None = None
    on_ground: bool | None = None

    status: str = "unknown"
    last_contact: datetime | None = None
    age_seconds: float | None = None
    is_stale: bool = False


class AircraftIdentity(ORMModel):
    icao24: str
    registration: str | None = None
    callsign: str | None = None
    type_code: str | None = None
    model: str | None = None
    operator: str | None = None
    country: str | None = None


class AircraftDetail(BaseModel):
    identity: AircraftIdentity
    position: StateVector | None = None
    status: str = "unknown"
    age_seconds: float | None = None
    is_stale: bool = False

    # route info, only filled when we actually have it
    departure_icao: str | None = None
    arrival_icao: str | None = None
    departure_name: str | None = None
    arrival_name: str | None = None
    departure_iata: str | None = None
    arrival_iata: str | None = None
    airline: str | None = None

    # photo comes from adsbdb and only when it actually has one
    photo_url: str | None = None
    photo_thumbnail: str | None = None
