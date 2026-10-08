-- SilentSOS postgres connectivity probe.
--
-- NOTE: this file intentionally does NOT create the application schema.
-- Tables (users, locations, cameras, incidents, detection_events, alerts)
-- are owned by the backend (SQLAlchemy models + Alembic migrations), so the
-- schema can never drift between this file and the ORM. This table only
-- proves the postgres service booted and accepts connections.

CREATE TABLE IF NOT EXISTS _level1_ready (
  id SERIAL PRIMARY KEY,
  checked_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO _level1_ready DEFAULT VALUES;
