from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

connect_args = {}
if _is_sqlite:
    # sqlite connections aren't shared across the threadpool fastapi uses
    connect_args["check_same_thread"] = False
    connect_args["timeout"] = 30  # seconds to wait on a locked db

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        # WAL lets readers keep going while the background persist writes,
        # and the busy timeout makes a writer wait instead of failing the
        # instant the db is busy. without these the persist pass (which
        # touches thousands of aircraft) locks out api reads.
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
