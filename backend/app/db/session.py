"""DB engine + session.

The inference thread (stream.py) and the notifier thread both write incidents
while HTTP request handlers read them. With SQLite that means concurrent
access to one file, so we:

  - enable WAL, which lets readers run while a writer holds the lock;
  - set a busy_timeout so a writer waits instead of raising "database is
    locked" straight away;
  - keep a bounded pool rather than opening a new connection per query.

Postgres needs none of this and keeps the normal pooled configuration.
"""
import time

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from ..core.config import settings

_IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

if _IS_SQLITE:
    engine = create_engine(
        settings.DATABASE_URL,
        # Inference and request threads use different sessions; each session
        # still only ever touches one connection from its own thread.
        connect_args={"check_same_thread": False, "timeout": 15},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        """WAL + busy timeout so concurrent readers/writers coexist."""
        cur = dbapi_conn.cursor()
        # WAL: readers no longer block on the writer.
        cur.execute("PRAGMA journal_mode=WAL")
        # Wait rather than fail when another thread holds the write lock.
        cur.execute("PRAGMA busy_timeout=15000")
        # Enforce FK constraints (off by default in SQLite).
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# SQLite raises "database is locked" rather than waiting past busy_timeout
# when a long write overlaps. Retry a few times before surfacing the failure.
_WRITE_RETRIES = 3


def commit_with_retry(db) -> None:
    """Commit, retrying transient SQLite lock contention."""
    for attempt in range(_WRITE_RETRIES):
        try:
            db.commit()
            return
        except OperationalError as exc:
            db.rollback()
            if "locked" not in str(exc).lower() or attempt == _WRITE_RETRIES - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
