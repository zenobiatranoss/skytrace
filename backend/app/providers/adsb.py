import asyncio
from datetime import timedelta

import httpx

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import Bounds, FlightDataProvider
from app.schemas.aircraft import StateVector
from app.utils.coordinates import haversine_km
from app.utils.time import from_epoch, utcnow
from app.utils.validation import clean_icao24, normalize_callsign

log = get_logger(__name__)

# readsb reports in aviation units, we keep everything metric
FT_TO_M = 0.3048
FPM_TO_MS = 0.00508
KT_TO_MS = 0.514444

# a point query with a globe-spanning radius returns everything, so this
# only guards against silly config values, not a real feed limit
MAX_RADIUS_NM = 20000


def _as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class ReadsbJsonProvider(FlightDataProvider):
    """base for readsb/tar1090 style json feeds.

    these aggregate ADS-B receivers directly, so the data is closer to the
    raw broadcast than opensky's. there's no whole-world endpoint, so a feed
    needs an area: the opensky box when we have one, otherwise the
    configured center and radius. how far one query reaches is a per-feed
    thing (see max_radius_nm)."""

    name = "readsb"
    base_url = "https://api.adsb.lol"
    # {base}, {lat}, {lon} and {radius} get filled in
    point_path = "{base}/v2/point/{lat}/{lon}/{radius}"
    military_path: str | None = "{base}/v2/mil"
    # the json key holding the aircraft array
    array_key = "ac"
    # feeds differ here: adsb.lol serves the globe in one call, adsb.fi
    # stops at 250nm and errors past it
    max_radius_nm = MAX_RADIUS_NM

    def __init__(self, base_url: str | None = None) -> None:
        self._client: httpx.AsyncClient | None = None
        self._base = base_url or self.base_url

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=settings.opensky_timeout,
                headers={"User-Agent": settings.adsb_user_agent},
            )
        return self._client

    def _resolve_area(self, bounds: Bounds | None) -> tuple[float, float, int] | None:
        if bounds:
            lamin, lomin, lamax, lomax = bounds
            clat = (lamin + lamax) / 2
            clon = (lomin + lomax) / 2
            radius_km = max(
                haversine_km(clat, clon, lamax, lomax),
                haversine_km(clat, clon, lamin, lomin),
            )
            radius_nm = int(radius_km / 1.852) + 1
        else:
            center = settings.adsb_center_tuple
            if center is None:
                return None
            clat, clon = center
            radius_nm = settings.adsb_radius_nm

        # a feed that can't reach this far would only return a useless
        # sliver, so we skip it rather than send a request it rejects
        if radius_nm > self.max_radius_nm:
            log.debug(
                "%s: area needs %dnm but this feed caps at %dnm, skipping",
                self.name,
                radius_nm,
                self.max_radius_nm,
            )
            return None
        return clat, clon, max(radius_nm, 1)

    async def fetch_states(self, bounds: Bounds | None = None) -> list[StateVector]:
        targets: list[tuple[str, tuple[float, float, int] | None]] = []

        area = self._resolve_area(bounds)
        if area is not None:
            targets.append(("point", area))
        if self.military_path and settings.adsb_military:
            targets.append(("mil", None))

        if not targets:
            return []

        client = await self._http()
        results = await asyncio.gather(
            *(self._request(client, kind, area) for kind, area in targets),
            return_exceptions=True,
        )

        states: list[StateVector] = []
        errors: list[Exception] = []
        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
                continue
            states.extend(result)

        # one dead feed shouldn't sink the whole source
        if not states and errors:
            raise errors[0]
        if errors:
            log.warning(
                "%s: %d of %d feeds failed", self.name, len(errors), len(targets)
            )
        return self._dedupe(states)

    async def _request(
        self,
        client: httpx.AsyncClient,
        kind: str,
        area: tuple[float, float, int] | None,
    ) -> list[StateVector]:
        if kind == "point" and area is not None:
            lat, lon, radius = area
            url = self.point_path.format(
                base=self._base, lat=f"{lat:.4f}", lon=f"{lon:.4f}", radius=radius
            )
        elif self.military_path:
            url = self.military_path.format(base=self._base)
        else:
            return []

        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ProviderError(self.name, "rate limit hit") from exc
            raise ProviderError(
                self.name, f"{kind} request failed ({exc.response.status_code})"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"{kind} request failed: {exc}") from exc

        body = resp.json() or {}
        now = self._now(body)
        rows = body.get(self.array_key) or []
        parsed = [self._parse_aircraft(row, now) for row in rows]
        return [s for s in parsed if s is not None]

    def _now(self, body: dict):
        now_ms = _as_float(body.get("now"))
        if now_ms is None:
            return utcnow()
        return from_epoch(now_ms / 1000)

    def _parse_aircraft(self, row: dict, now) -> StateVector | None:
        if not isinstance(row, dict):
            return None

        icao24 = clean_icao24(row.get("hex"))
        if icao24 is None:
            return None

        altitude_m: float | None = None
        on_ground: bool | None = None
        alt_baro = row.get("alt_baro")
        if alt_baro == "ground":
            on_ground = True
        else:
            feet = _as_float(alt_baro)
            if feet is not None:
                altitude_m = feet * FT_TO_M
                # a numeric barometric altitude means it's airborne
                on_ground = False

        geo_feet = _as_float(row.get("alt_geom"))
        geo_altitude_m = geo_feet * FT_TO_M if geo_feet is not None else None

        gs = _as_float(row.get("gs"))
        velocity_ms = gs * KT_TO_MS if gs is not None else None

        rate = _as_float(row.get("baro_rate"))
        if rate is None:
            rate = _as_float(row.get("geom_rate"))
        vertical_rate_ms = rate * FPM_TO_MS if rate is not None else None

        seen = _as_float(row.get("seen"))
        seen_pos = _as_float(row.get("seen_pos"))
        last_contact = now - timedelta(seconds=seen) if seen is not None else now
        time_position = (
            now - timedelta(seconds=seen_pos) if seen_pos is not None else None
        )

        return StateVector(
            icao24=icao24,
            callsign=normalize_callsign(row.get("flight")),
            latitude=_as_float(row.get("lat")),
            longitude=_as_float(row.get("lon")),
            altitude_m=altitude_m,
            geo_altitude_m=geo_altitude_m,
            velocity_ms=velocity_ms,
            heading=_as_float(row.get("track")),
            vertical_rate_ms=vertical_rate_ms,
            on_ground=on_ground,
            squawk=(row.get("squawk") or None),
            time_position=time_position,
            last_contact=last_contact,
        )

    def _dedupe(self, states: list[StateVector]) -> list[StateVector]:
        by_icao: dict[str, StateVector] = {}
        for state in states:
            by_icao.setdefault(state.icao24, state)
        return list(by_icao.values())

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class AdsbLolProvider(ReadsbJsonProvider):
    """adsb.lol - the global one. big radius works, so we get the whole
    world from a single point query."""

    name = "adsb"
    base_url = "https://api.adsb.lol"


class AdsbFiProvider(ReadsbJsonProvider):
    """adsb.fi's open data feed. different path shape, richer fields, but
    it only reaches 250nm per query, so it's a regional add-on."""

    name = "adsbfi"
    base_url = "https://opendata.adsb.fi"
    point_path = "{base}/api/v2/lat/{lat}/lon/{lon}/dist/{radius}"
    military_path = None
    array_key = "aircraft"
    max_radius_nm = 250
