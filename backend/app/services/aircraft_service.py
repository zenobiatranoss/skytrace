from sqlalchemy.orm import Session

from app.cache.aircraft_cache import aircraft_cache
from app.cache.response_cache import response_cache
from app.core.config import settings
from app.core.errors import NotFoundError, ProviderError
from app.core.logging import get_logger
from app.providers.adsbdb import AircraftInfo, RouteAirport, RouteInfo, get_adsbdb_provider
from app.providers.flight_data import get_route_provider
from app.repositories import aircraft_repository, flight_repository
from app.schemas.aircraft import AircraftDetail, AircraftIdentity
from app.services import position_service
from app.utils.flight_status import derive_status
from app.utils.time import age_seconds

log = get_logger(__name__)

ROUTE_CACHE_TTL = 300


def _callsign_for(db: Session, icao24: str, flight) -> str | None:
    state = aircraft_cache.get(icao24)
    if state and state.callsign:
        return state.callsign
    if flight and flight.callsign:
        return flight.callsign
    row = aircraft_repository.get_by_icao24(db, icao24)
    return row.callsign if row else None


async def _route_info(db: Session, icao24: str) -> RouteInfo | None:
    """route for the callsign we're seeing. adsbdb knows most airline
    routes and gives us real airport names; opensky's history is a weaker
    fallback. whatever we learn gets pinned to the flight row."""
    flight = flight_repository.get_active_for_aircraft(db, icao24)
    callsign = _callsign_for(db, icao24, flight)

    cache_key = f"route:{callsign or icao24}"
    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached

    info = None
    if settings.adsbdb_enabled:
        try:
            info = await get_adsbdb_provider().get_route(callsign)
        except ProviderError as exc:
            log.warning("adsbdb route lookup failed for %s: %s", callsign or icao24, exc)

    if info is None:
        info = await _opensky_route(icao24)

    if flight is not None and info is not None:
        origin = info.origin.icao if info.origin else None
        destination = info.destination.icao if info.destination else None
        if origin or destination:
            flight.departure_icao = origin or flight.departure_icao
            flight.arrival_icao = destination or flight.arrival_icao
            db.commit()

    response_cache.set(cache_key, info, ttl=ROUTE_CACHE_TTL)
    return info


async def _opensky_route(icao24: str) -> RouteInfo | None:
    try:
        legacy = await get_route_provider().get_route(icao24)
    except ProviderError as exc:
        log.warning("route lookup failed for %s: %s", icao24, exc)
        return None
    if legacy is None:
        return None
    return RouteInfo(
        callsign=legacy.callsign,
        airline=None,
        origin=_icao_airport(legacy.departure_icao),
        destination=_icao_airport(legacy.arrival_icao),
    )


def _icao_airport(icao: str | None) -> RouteAirport | None:
    if not icao:
        return None
    return RouteAirport(
        icao=icao, iata=None, name=None, municipality=None, latitude=None, longitude=None
    )


async def _aircraft_info(icao24: str) -> AircraftInfo | None:
    if not settings.adsbdb_enabled:
        return None
    try:
        return await get_adsbdb_provider().get_aircraft(icao24)
    except ProviderError as exc:
        log.warning("adsbdb aircraft lookup failed for %s: %s", icao24, exc)
        return None


def _merge_identity(identity: AircraftIdentity, info: AircraftInfo) -> AircraftIdentity:
    return identity.model_copy(
        update={
            "registration": identity.registration or info.registration,
            "type_code": identity.type_code or info.type_code,
            "model": identity.model or info.model,
            "operator": identity.operator or info.operator,
        }
    )


def _persist_identity(db: Session, row, info: AircraftInfo) -> None:
    changed = False
    for field in ("registration", "type_code", "model", "operator"):
        if not getattr(row, field) and getattr(info, field):
            setattr(row, field, getattr(info, field))
            changed = True
    if changed:
        db.commit()


async def get_detail(db: Session, icao24: str) -> AircraftDetail:
    icao24 = icao24.lower()
    state = aircraft_cache.get(icao24)
    row = aircraft_repository.get_by_icao24(db, icao24)

    if state is None and row is None:
        raise NotFoundError(f"aircraft {icao24}")

    info = await _aircraft_info(icao24)

    if row is not None:
        identity = AircraftIdentity.model_validate(row)
        if info is not None:
            _persist_identity(db, row, info)
    else:
        identity = AircraftIdentity(
            icao24=icao24,
            callsign=state.callsign if state else None,
            country=state.origin_country if state else None,
        )
    if info is not None:
        identity = _merge_identity(identity, info)

    age = None
    status = "unknown"
    if state is not None:
        age = age_seconds(state.last_contact)
        if age is None:
            age = aircraft_cache.age_of(icao24)
        status = derive_status(
            state.on_ground, age, settings.position_stale_seconds
        ).value

    route = await _route_info(db, icao24)

    return AircraftDetail(
        identity=identity,
        position=state,
        status=status,
        age_seconds=age,
        is_stale=age is not None and age > settings.position_stale_seconds,
        departure_icao=route.origin.icao if route and route.origin else None,
        arrival_icao=route.destination.icao if route and route.destination else None,
        departure_name=route.origin.name if route and route.origin else None,
        arrival_name=route.destination.name if route and route.destination else None,
        departure_iata=route.origin.iata if route and route.origin else None,
        arrival_iata=route.destination.iata if route and route.destination else None,
        airline=route.airline if route else None,
        photo_url=info.photo_url if info else None,
        photo_thumbnail=info.photo_thumbnail if info else None,
    )


def get_position(db: Session, icao24: str):
    position = position_service.get_position(db, icao24)
    if position is None:
        raise NotFoundError(f"aircraft {icao24}")
    return position
