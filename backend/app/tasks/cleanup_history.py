from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.services import flight_history_service
from app.utils.time import utcnow

log = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def cleanup_history() -> None:
    """trim old track points and dead flight rows"""
    db = SessionLocal()
    try:
        points = flight_history_service.purge_old_points(db)
        flights = flight_history_service.purge_orphan_flights(db)
        anomalies = flight_history_service.purge_old_anomalies(db)
        log.info(
            "cleanup removed %d points, %d flights, %d anomalies",
            points,
            flights,
            anomalies,
        )
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler()
    # hourly is plenty at this scale
    scheduler.add_job(
        cleanup_history,
        "interval",
        hours=1,
        next_run_time=utcnow(),
        id="cleanup_history",
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
