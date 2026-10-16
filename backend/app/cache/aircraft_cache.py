from datetime import datetime

from app.schemas.aircraft import StateVector
from app.utils.time import age_seconds, utcnow


class AircraftCache:
    """keeps the latest state vector per aircraft in memory.

    every client reads from here, so we never fan out to the provider per
    request. positions only ever get replaced, not appended - history lives
    in the database.
    """

    def __init__(self) -> None:
        self._states: dict[str, StateVector] = {}
        self._received_at: dict[str, datetime] = {}
        self.updated_at: datetime | None = None

    def replace_all(self, states: list[StateVector]) -> None:
        now = utcnow()
        fresh: dict[str, StateVector] = {}
        stamps: dict[str, datetime] = {}
        for state in states:
            fresh[state.icao24] = state
            stamps[state.icao24] = now

        self._states = fresh
        self._received_at = stamps
        self.updated_at = now

    def merge(self, states: list[StateVector], retain_seconds: float = 0.0) -> None:
        """swap in the new snapshot but keep recently-seen aircraft that this
        cycle happened to miss. feeds are lossy and aircraft would otherwise
        blink in and out every poll; we'd rather show a slightly old dot
        (it gets flagged stale) than drop it between two sightings."""
        now = utcnow()
        fresh: dict[str, StateVector] = {s.icao24: s for s in states}
        stamps: dict[str, datetime] = {s.icao24: now for s in states}

        if retain_seconds > 0:
            for icao, state in self._states.items():
                if icao in fresh:
                    continue
                received = self._received_at.get(icao)
                if received is not None and age_seconds(received) <= retain_seconds:
                    fresh[icao] = state
                    stamps[icao] = received

        self._states = fresh
        self._received_at = stamps
        self.updated_at = now

    def get(self, icao24: str) -> StateVector | None:
        return self._states.get(icao24.lower())

    def received_at(self, icao24: str) -> datetime | None:
        return self._received_at.get(icao24.lower())

    def all(self) -> list[StateVector]:
        return list(self._states.values())

    def in_bounds(self, bounds: tuple[float, float, float, float]) -> list[StateVector]:
        lamin, lomin, lamax, lomax = bounds
        result = []
        for state in self._states.values():
            if state.latitude is None or state.longitude is None:
                continue
            if lamin <= state.latitude <= lamax and lomin <= state.longitude <= lomax:
                result.append(state)
        return result

    def size(self) -> int:
        return len(self._states)

    def age_of(self, icao24: str) -> float | None:
        return age_seconds(self.received_at(icao24))

    def clear(self) -> None:
        self._states.clear()
        self._received_at.clear()
        self.updated_at = None


# one process-wide cache is fine at this size
aircraft_cache = AircraftCache()
