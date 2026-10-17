import asyncio
import time

from app.cache.aircraft_cache import aircraft_cache
from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.data_source import DataSourceRun
from app.providers.aircraft_data import get_aircraft_provider
from app.repositories import aircraft_repository, flight_repository
from app.services import anomaly_service, position_service, track_service
from app.utils.time import utcnow

log = get_logger(__name__)

# persist roughly once a minute regardless of the poll interval
PERSIST_EVERY_SECONDS = 60


async def refresh_once() -> list:
    """one poll of the provider plus a cache swap. returns the fresh states
    (empty list means the provider had nothing for us)."""
    states = await position_service.get_provider().fetch_states(
        settings.opensky_bounds_tuple
    )
    # keep recently seen aircraft that this poll missed, so a lossy feed
    # doesn't make them flicker off the map
    aircraft_cache.merge(states, retain_seconds=settings.position_stale_seconds)
    return states


def persist_snapshot() -> None:
    """write the current cache down to sqlite: refresh identities, keep the
    active flight moving, and drop a track point where it's due."""
    now = utcnow()
    states = aircraft_cache.all()
    if not states:
        return

    metadata = get_aircraft_provider()
    metadata.load()

    db = SessionLocal()
    try:
        for state in states:
            aircraft = aircraft_repository.touch_from_state(db, state, now=now)

            meta = metadata.get(state.icao24)
            if meta is not None:
                aircraft_repository.apply_metadata(aircraft, meta)

            flight = flight_repository.upsert_active(db, state, now=now)
            db.flush()  # need flight.id for the track point
            track_service.maybe_record(db, flight, state, now=now)

        db.commit()
    except Exception:
        db.rollback()
        log.exception("persist snapshot failed")
    finally:
        db.close()


def _record_run(status: str, records: int, duration_ms: int, error: str | None) -> None:
    provider = "+".join(position_service.active_sources()) or "none"
    db = SessionLocal()
    try:
        db.add(
            DataSourceRun(
                provider=provider,
                status=status,
                records=records,
                duration_ms=duration_ms,
                error=error,
            )
        )
        db.commit()
    finally:
        db.close()


class RefreshLoop:
    """the background poller. runs forever until stopped, respecting the
    provider's rate limits by only ever making one call per interval."""

    def __init__(self, interval: int | None = None) -> None:
        self.interval = interval or settings.position_refresh_seconds
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self.last_error: str | None = None
        self._last_persist = 0.0

    async def _tick(self) -> None:
        started = time.monotonic()
        try:
            states = await refresh_once()
            elapsed_ms = int((time.monotonic() - started) * 1000)
            self.last_error = None
            _record_run("ok", len(states), elapsed_ms, None)

            from app.websocket.flight_updates import (
                broadcast_anomalies,
                broadcast_positions,
            )

            await broadcast_positions()

            if settings.anomaly_enabled:
                # detection + the db write are blocking, keep them off the loop
                views = await asyncio.to_thread(anomaly_service.evaluate_cycle, states)
                await broadcast_anomalies(views)

            log.debug("refreshed %d states in %dms", len(states), elapsed_ms)
        except ProviderError as exc:
            self.last_error = str(exc)
            _record_run("error", 0, int((time.monotonic() - started) * 1000), str(exc))
            log.warning("position refresh failed: %s", exc)
        except Exception:
            self.last_error = "unexpected refresh error"
            _record_run(
                "error", 0, int((time.monotonic() - started) * 1000), "unexpected"
            )
            log.exception("unexpected error during refresh")

        now = time.monotonic()
        if now - self._last_persist >= PERSIST_EVERY_SECONDS:
            self._last_persist = now
            # sqlite writes are blocking, keep them off the event loop
            await asyncio.to_thread(persist_snapshot)

    async def _run(self) -> None:
        while not self._stop.is_set():
            await self._tick()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
            except TimeoutError:
                pass

    def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
            self._task = None


refresh_loop = RefreshLoop()
