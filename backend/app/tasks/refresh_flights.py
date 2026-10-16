from app.core.logging import get_logger
from app.services import data_refresh_service

log = get_logger(__name__)


async def refresh_flights() -> int:
    """one-shot refresh, for running outside the background loop (cron,
    a manual trigger, tests). returns how many states we pulled."""
    states = await data_refresh_service.refresh_once()
    log.info("manual refresh pulled %d states", len(states))
    return len(states)
