-- SilentSOS Level 1 dev init. Full schema (users, locations, cameras,
-- incidents, detection_events, alerts) lands in Level 2.
-- This keeps `docker compose up postgres` working for Level-1 connectivity test.

CREATE TABLE IF NOT EXISTS _level1_ready (
  id SERIAL PRIMARY KEY,
  checked_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO _level1_ready DEFAULT VALUES;
