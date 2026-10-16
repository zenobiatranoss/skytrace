import csv
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class AirportRecord:
    __slots__ = ("icao", "iata", "name", "city", "country", "lat", "lon", "elevation_ft")

    def __init__(self, icao, iata, name, city, country, lat, lon, elevation_ft):
        self.icao = icao
        self.iata = iata
        self.name = name
        self.city = city
        self.country = country
        self.lat = lat
        self.lon = lon
        self.elevation_ft = elevation_ft


class AirportDataProvider:
    """reads a local OurAirports csv export.

    we deliberately don't ship a baked-in airport list - if the dataset isn't
    configured we return nothing rather than inventing airports.
    """

    name = "airports"

    def __init__(self, path: str | None = None) -> None:
        self.path = path or settings.airports_dataset_path
        self._by_icao: dict[str, AirportRecord] = {}
        self._by_iata: dict[str, AirportRecord] = {}
        self._loaded = False

    def is_available(self) -> bool:
        return bool(self.path) and Path(self.path).exists()

    def load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        if not self.is_available():
            log.info("no airports dataset configured, airport lookups disabled")
            return

        count = 0
        with open(self.path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # only keep things you could actually fly to
                if row.get("type") not in {"large_airport", "medium_airport", "small_airport"}:
                    continue
                try:
                    lat = float(row["latitude_deg"])
                    lon = float(row["longitude_deg"])
                except (KeyError, ValueError):
                    continue

                elev = row.get("elevation_ft") or ""
                record = AirportRecord(
                    icao=(row.get("ident") or "").upper() or None,
                    iata=(row.get("iata_code") or "").upper() or None,
                    name=row.get("name") or "",
                    city=(row.get("municipality") or "") or None,
                    country=(row.get("iso_country") or "") or None,
                    lat=lat,
                    lon=lon,
                    elevation_ft=float(elev) if elev else None,
                )

                if record.icao:
                    self._by_icao[record.icao] = record
                if record.iata:
                    self._by_iata[record.iata] = record
                count += 1

        log.info("loaded %d airports from dataset", count)

    def get(self, code: str | None) -> AirportRecord | None:
        if not code:
            return None
        code = code.upper()
        return self._by_icao.get(code) or self._by_iata.get(code)

    def search(self, query: str, limit: int = 10) -> list[AirportRecord]:
        self.load()
        q = query.strip().lower()
        if not q:
            return []

        hits: list[AirportRecord] = []
        for record in self._by_icao.values():
            haystack = " ".join(
                filter(None, [record.icao, record.iata, record.name, record.city])
            ).lower()
            if q in haystack:
                hits.append(record)
            if len(hits) >= limit:
                break
        return hits


@lru_cache
def get_airport_provider() -> AirportDataProvider:
    return AirportDataProvider()
