import os

# keep tests off the real database and out of the provider's rate budget.
# env vars win over the repo .env, so we pin the source too.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_skytrace.db")
os.environ.setdefault("POSITION_REFRESH_SECONDS", "3600")
os.environ.setdefault("POSITION_SOURCES", "opensky")
os.environ.setdefault("ADSBDB_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.cache.aircraft_cache import aircraft_cache
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.main import app
from app.schemas.aircraft import StateVector
from app.utils.time import from_epoch, utcnow


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_cache():
    aircraft_cache.clear()
    yield
    aircraft_cache.clear()


@pytest.fixture
def client():
    # note: no context manager, so the lifespan (and the live poller) is skipped
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_state() -> StateVector:
    now = from_epoch(int(utcnow().timestamp()))
    return StateVector(
        icao24="39de57",
        callsign="TVF431J",
        origin_country="France",
        latitude=54.2975,
        longitude=10.928,
        altitude_m=11582.4,
        velocity_ms=230.1,
        heading=218.89,
        vertical_rate_ms=0.0,
        on_ground=False,
        last_contact=now,
        time_position=now,
    )
