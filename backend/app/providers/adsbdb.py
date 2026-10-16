import time
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger

log = get_logger(__name__)

# routes and frames barely change, so we can hold them for a long time.
# misses get a shorter life so a new airline callsign eventually resolves.
ROUTE_TTL = 6 * 3600
AIRCRAFT_TTL = 24 * 3600
MISS_TTL = 3600


@dataclass
class RouteAirport:
    icao: str | None
    iata: str | None
    name: str | None
    municipality: str | None
    latitude: float | None
    longitude: float | None


@dataclass
class RouteInfo:
    callsign: str | None
    airline: str | None
    origin: RouteAirport | None
    destination: RouteAirport | None


@dataclass
class AircraftInfo:
    icao24: str
    registration: str | None
    type_code: str | None
    model: str | None
    operator: str | None
    photo_url: str | None
    photo_thumbnail: str | None


def _str(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _airport(data: dict | None) -> RouteAirport | None:
    if not isinstance(data, dict):
        return None
    return RouteAirport(
        icao=_str(data.get("icao_code")),
        iata=_str(data.get("iata_code")),
        name=_str(data.get("name")),
        municipality=_str(data.get("municipality")),
        latitude=_float(data.get("latitude")),
        longitude=_float(data.get("longitude")),
    )


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class AdsbDbProvider:
    """adsbdb - free lookup for routes, aircraft identity and photos.

    two plain json endpoints, no key. we cache hard because the data is
    essentially static: a callsign's route doesn't move, and a frame keeps
    its registration."""

    name = "adsbdb"

    def __init__(self, base_url: str | None = None) -> None:
        self._client: httpx.AsyncClient | None = None
        self._base = base_url or settings.adsbdb_base_url
        self._routes: dict[str, tuple[float, RouteInfo | None]] = {}
        self._aircraft: dict[str, tuple[float, AircraftInfo | None]] = {}

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=settings.adsbdb_timeout,
                headers={"User-Agent": settings.adsb_user_agent},
            )
        return self._client

    async def _get(self, url: str) -> dict | None:
        client = await self._http()
        try:
            resp = await client.get(url)
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"request failed: {exc}") from exc

        if resp.status_code == 404:
            return None
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                self.name, f"request failed ({exc.response.status_code})"
            ) from exc

        body = resp.json()
        return body if isinstance(body, dict) else None

    async def get_route(self, callsign: str | None) -> RouteInfo | None:
        if not callsign:
            return None
        key = callsign.strip().upper()
        hit = self._routes.get(key)
        if hit is not None and time.time() < hit[0]:
            return hit[1]

        body = await self._get(f"{self._base}/v0/callsign/{key}")
        route = self._parse_route(body)
        ttl = ROUTE_TTL if route is not None else MISS_TTL
        self._routes[key] = (time.time() + ttl, route)
        return route

    def _parse_route(self, body: dict | None) -> RouteInfo | None:
        if not body:
            return None
        response = body.get("response")
        if not isinstance(response, dict):
            return None
        route = response.get("flightroute")
        if not isinstance(route, dict):
            return None

        airline = route.get("airline")
        airline_name = _str(airline.get("name")) if isinstance(airline, dict) else None
        return RouteInfo(
            callsign=_str(route.get("callsign")),
            airline=airline_name,
            origin=_airport(route.get("origin")),
            destination=_airport(route.get("destination")),
        )

    async def get_aircraft(self, icao24: str | None) -> AircraftInfo | None:
        if not icao24:
            return None
        key = icao24.strip().lower()
        hit = self._aircraft.get(key)
        if hit is not None and time.time() < hit[0]:
            return hit[1]

        body = await self._get(f"{self._base}/v0/aircraft/{key}")
        info = self._parse_aircraft(key, body)
        ttl = AIRCRAFT_TTL if info is not None else MISS_TTL
        self._aircraft[key] = (time.time() + ttl, info)
        return info

    def _parse_aircraft(self, icao24: str, body: dict | None) -> AircraftInfo | None:
        if not body:
            return None
        response = body.get("response")
        if not isinstance(response, dict):
            return None
        aircraft = response.get("aircraft")
        if not isinstance(aircraft, dict):
            return None

        manufacturer = _str(aircraft.get("manufacturer"))
        raw_type = _str(aircraft.get("type"))
        if manufacturer and raw_type:
            model = f"{manufacturer} {raw_type}"
        else:
            model = raw_type or manufacturer

        return AircraftInfo(
            icao24=icao24,
            registration=_str(aircraft.get("registration")),
            type_code=_str(aircraft.get("icao_type")),
            model=model,
            operator=_str(aircraft.get("registered_owner")),
            photo_url=_str(aircraft.get("url_photo")),
            photo_thumbnail=_str(aircraft.get("url_photo_thumbnail")),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


_provider: AdsbDbProvider | None = None


def get_adsbdb_provider() -> AdsbDbProvider:
    global _provider
    if _provider is None:
        _provider = AdsbDbProvider()
    return _provider
