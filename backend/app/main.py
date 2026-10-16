from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import get_logger, setup_logging
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.services import anomaly_service, data_refresh_service, position_service
from app.tasks.cleanup_history import start_scheduler, stop_scheduler
from app.websocket.flight_updates import send_status
from app.websocket.manager import manager

# models have to be imported so they're registered on the metadata
import app.models  # noqa: F401

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    Base.metadata.create_all(bind=engine)
    log.info("%s starting up", settings.app_name)

    # any anomalies left open from a previous run get re-detected shortly,
    # so close them now instead of showing stale flags
    db = SessionLocal()
    try:
        closed = anomaly_service.reset(db)
        if closed:
            log.info("closed %d stale anomalies from previous run", closed)
    finally:
        db.close()

    data_refresh_service.refresh_loop.start()
    start_scheduler()
    try:
        yield
    finally:
        await data_refresh_service.refresh_loop.stop()
        stop_scheduler()
        await position_service.close_provider()
        log.info("%s shut down", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router)


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """live position feed. the client just listens; we push on each refresh."""
    await manager.connect(websocket)
    try:
        await send_status(websocket)
        while True:
            # we don't expect messages, but reading lets us notice a disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
