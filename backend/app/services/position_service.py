from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache.aircraft_cache import aircraft_cache
from app.core.config import settings
from app.core.logging import get_logger
from app.models.aircraft import Aircraft
from app.providers.adsb import AdsbFiProvider, AdsbLolProvider
from app.providers.base import Bounds, FlightDataProvider
from app.providers.multi import MultiSourceProvider
from app.providers.opensky import OpenSkyProvider
from app.schemas.aircraft import AircraftPosition, StateVector
from app.utils.flight_status import derive_status
from app.utils.time import age_seconds

log = get_logger(__name__)

_KNOWN_SOURCES = {
    "opensky": lambda: OpenSkyProvider(),
    "adsb": lambda: AdsbLolProvider(settings.adsb_base_url),
    "adsbfi": lambda: AdsbFiProvider(settings.adsbfi_base_url),
}

_provider: FlightDataProvider | None = None


def _build_provider() -> FlightDataProvider:
    providers: list[FlightDataProvider] = []
    for name in settings.position_source_list:
        factory = _KNOWN_SOURCES.get(name)
        if factory is None:
            log.warning("unknown position source %r, skipping", name)
            continue
        providers.append(factory())

    if not providers:
        providers = [OpenSkyProvider()]
    if len(providers) == 1:
        return providers[0]
    return MultiSourceProvider(providers)


def get_provider() -> FlightDataProvider:
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def active_sources() -> list[str]:
    """names of the feeds currently feeding the cache, for run records"""
    provider = get_provider()
    if isinstance(provider, MultiSourceProvider):
        return provider.source_names
    return [provider.name]


async def close_provider() -> None:
    global _provider
    if _provider is not None:
        await _provider.close()
        _provider = None


async def refresh_positions(bounds: Bounds | None = None) -> int:
    """pull fresh positions and swap them into the cache. returns how many
    we got, so the caller can log or react to an empty result."""
    states = await get_provider().fetch_states(bounds)
    aircraft_cache.merge(states, retain_seconds=settings.position_stale_seconds)
    return len(states)


def _freshness_age(state: StateVector) -> float | None:
    # prefer the source timestamp; fall back to when we received it
    age = age_seconds(state.last_contact)
    if age is None:
        age = aircraft_cache.age_of(state.icao24)
    return age


def _to_position(state: StateVector, identity: Aircraft | None) -> AircraftPosition:
    age = _freshness_age(state)
    stale = age is not None and age > settings.position_stale_seconds
    status = derive_status(state.on_ground, age, settings.position_stale_seconds)

    return AircraftPosition(
        icao24=state.icao24,
        callsign=state.callsign or (identity.callsign if identity else None),
        registration=identity.registration if identity else None,
        type_code=identity.type_code if identity else None,
        latitude=state.latitude,
        longitude=state.longitude,
        altitude_m=state.altitude_m,
        velocity_ms=state.velocity_ms,
        heading=state.heading,
        vertical_rate_ms=state.vertical_rate_ms,
        on_ground=state.on_ground,
        status=status.value,
        last_contact=state.last_contact,
        age_seconds=age,
        is_stale=stale,
    )


def _identities(db: Session, icao24s: list[str]) -> dict[str, Aircraft]:
    if not icao24s:
        return {}
    stmt = select(Aircraft).where(Aircraft.icao24.in_(icao24s))
    return {a.icao24: a for a in db.scalars(stmt)}


def list_positions(
    db: Session,
    bounds: Bounds | None = None,
    limit: int | None = None,
) -> list[AircraftPosition]:
    states = aircraft_cache.in_bounds(bounds) if bounds else aircraft_cache.all()
    identities = _identities(db, [s.icao24 for s in states])

    positions = [_to_position(s, identities.get(s.icao24)) for s in states]
    # keep the ones we can actually draw on top
    positions.sort(key=lambda p: (p.is_stale, p.callsign is None))
    if limit is not None:
        positions = positions[:limit]
    return positions


def snapshot(bounds: Bounds | None = None) -> list[AircraftPosition]:
    """cache-only view, no database access. used for the websocket broadcast
    where we don't want to hit sqlite on every tick."""
    states = aircraft_cache.in_bounds(bounds) if bounds else aircraft_cache.all()
    return [_to_position(s, None) for s in states]


def get_position(db: Session, icao24: str) -> AircraftPosition | None:
    state = aircraft_cache.get(icao24)
    if state is None:
        return None
    identity = db.scalar(select(Aircraft).where(Aircraft.icao24 == icao24.lower()))
    return _to_position(state, identity)
