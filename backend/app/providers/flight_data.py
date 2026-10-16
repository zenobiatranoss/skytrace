from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class RouteInfo:
    departure_icao: str | None
    arrival_icao: str | None
    callsign: str | None


class FlightRouteProvider:
    """route lookup from OpenSky's per-aircraft flight history.

    this is best-effort: it only knows about flights in the last day or so,
    and the departure/arrival fields are estimates. when there's nothing
    useful we return None instead of a made up route."""

    name = "opensky-routes"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.opensky_timeout)
        return self._client

    async def get_route(self, icao24: str) -> RouteInfo | None:
        from app.utils.time import to_epoch, utcnow

        now = to_epoch(utcnow())
        begin = now - 24 * 3600

        client = await self._http()
        try:
            resp = await client.get(
                f"{settings.opensky_base_url}/flights/aircraft",
                params={"icao24": icao24, "begin": begin, "end": now},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"route lookup failed: {exc}") from exc

        flights = resp.json() or []
        if not flights:
            return None

        # the most recent segment is the one we care about
        latest = max(flights, key=lambda f: f.get("lastSeen", 0))
        return RouteInfo(
            departure_icao=(latest.get("estDepartureAirport") or None),
            arrival_icao=(latest.get("estArrivalAirport") or None),
            callsign=(latest.get("callsign") or "").strip() or None,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


_route_provider: FlightRouteProvider | None = None


def get_route_provider() -> FlightRouteProvider:
    global _route_provider
    if _route_provider is None:
        _route_provider = FlightRouteProvider()
    return _route_provider
