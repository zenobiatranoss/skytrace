import time

import httpx

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import Bounds, FlightDataProvider
from app.schemas.aircraft import StateVector
from app.utils.time import from_epoch
from app.utils.validation import clean_icao24, normalize_callsign

log = get_logger(__name__)


def _as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class OpenSkyProvider(FlightDataProvider):
    """positions from the OpenSky Network.

    anonymous access works but is heavily rate limited, so credentials are
    picked up from settings when present. we only ever ask for the whole
    world (or a box) in one call - never one request per aircraft.
    """

    name = "opensky"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.opensky_timeout)
        return self._client

    def _has_credentials(self) -> bool:
        return bool(settings.opensky_client_id and settings.opensky_client_secret)

    async def _access_token(self) -> str | None:
        if not self._has_credentials():
            return None
        # reuse the token until it's a minute from expiring
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        client = await self._http()
        try:
            resp = await client.post(
                settings.opensky_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.opensky_client_id,
                    "client_secret": settings.opensky_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"token request failed: {exc}") from exc

        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 1800)
        return self._token

    async def fetch_states(self, bounds: Bounds | None = None) -> list[StateVector]:
        params: dict[str, float] = {}
        if bounds:
            lamin, lomin, lamax, lomax = bounds
            params = {
                "lamin": lamin,
                "lomin": lomin,
                "lamax": lamax,
                "lomax": lomax,
            }

        headers = {}
        token = await self._access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        client = await self._http()
        try:
            resp = await client.get(
                f"{settings.opensky_base_url}/states/all",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ProviderError(self.name, "rate limit hit") from exc
            raise ProviderError(
                self.name, f"states request failed ({exc.response.status_code})"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"states request failed: {exc}") from exc

        body = resp.json()
        states = body.get("states") or []
        parsed = [self._parse_state(row) for row in states]
        return [s for s in parsed if s is not None]

    def _parse_state(self, row: list) -> StateVector | None:
        if not row or len(row) < 17:
            return None

        icao24 = clean_icao24(row[0])
        if icao24 is None:
            return None

        return StateVector(
            icao24=icao24,
            callsign=normalize_callsign(row[1]),
            origin_country=row[2],
            latitude=_as_float(row[6]),
            longitude=_as_float(row[5]),
            altitude_m=_as_float(row[7]),
            geo_altitude_m=_as_float(row[13]),
            velocity_ms=_as_float(row[9]),
            heading=_as_float(row[10]),
            vertical_rate_ms=_as_float(row[11]),
            on_ground=row[8] if isinstance(row[8], bool) else None,
            squawk=row[14] or None,
            position_source=row[16] if isinstance(row[16], int) else None,
            time_position=from_epoch(row[3]),
            last_contact=from_epoch(row[4]),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
