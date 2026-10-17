import csv
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class AircraftMetadata:
    __slots__ = ("icao24", "model", "operator", "registration", "type_code")

    def __init__(self, icao24, registration, type_code, model, operator):
        self.icao24 = icao24
        self.registration = registration
        self.type_code = type_code
        self.model = model
        self.operator = operator


class AircraftDataProvider:
    """reads a local opensky aircraft database csv export.

    same stance as the airport list: no baked-in data. without the file we
    just don't enrich identities rather than guessing registration numbers.
    """

    name = "aircraft"

    def __init__(self, path: str | None = None) -> None:
        self.path = path or settings.aircraft_dataset_path
        self._by_icao: dict[str, AircraftMetadata] = {}
        self._loaded = False

    def is_available(self) -> bool:
        return bool(self.path) and Path(self.path).exists()

    def load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        if not self.is_available():
            log.info("no aircraft dataset configured, identity enrichment off")
            return

        count = 0
        with open(self.path, newline="", encoding="utf-8") as fh:
            # header casing drifted between opensky exports, so normalise it
            reader = csv.DictReader(fh)
            reader.fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
            for row in reader:
                icao24 = (row.get("icao24") or "").strip().lower()
                if len(icao24) != 6:
                    continue

                self._by_icao[icao24] = AircraftMetadata(
                    icao24=icao24,
                    registration=_clean(row.get("registration")),
                    type_code=_clean(row.get("typecode")),
                    model=_clean(row.get("model")),
                    operator=_clean(row.get("operator")) or _clean(row.get("owner")),
                )
                count += 1

        log.info("loaded %d aircraft identities from dataset", count)

    def get(self, icao24: str | None) -> AircraftMetadata | None:
        if not icao24:
            return None
        return self._by_icao.get(icao24.lower())


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


@lru_cache
def get_aircraft_provider() -> AircraftDataProvider:
    return AircraftDataProvider()
