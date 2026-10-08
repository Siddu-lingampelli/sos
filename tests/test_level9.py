"""Level 9 hardening tests: health, retention, notifications, auth, validation."""
import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.health import HealthRegistry
from app.core import notifier
from app.core.config import settings
from app.schemas import IncidentCreate, UserCreate


def test_health_registry_overall():
    h = HealthRegistry()
    h.set("vision", "ok")
    assert h.overall() == "ok"
    h.set("audio", "degraded", "no mic")
    assert h.overall() == "degraded"
    h.set("database", "down")
    assert h.overall() == "down"
    h.clear("database")
    h.clear("audio")
    assert h.overall() == "ok"


def test_notifier_broadcasts_and_records(monkeypatch):
    sent = []
    recorded = []
    monkeypatch.setattr(notifier.bus, "broadcast_sync", lambda msg: sent.append(msg))
    monkeypatch.setattr(notifier, "_record_alert", lambda iid, ch, st: recorded.append((iid, ch, st)))

    notifier.notify_incident(
        {"event_type": "Fall", "confidence": 0.8, "track_id": 3, "evidence": []},
        incident_id=11,
    )

    assert sent and sent[0]["type"] == "notification"
    assert sent[0]["channel"] == "websocket"
    assert ("websocket" in [r[1] for r in recorded])


def test_retention_purges_only_old_resolved(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db import session as db_session
    from app.models import Base, Incident, IncidentStatus
    from app.core import retention

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestSession)

    old = datetime.now(timezone.utc) - timedelta(days=90)
    db = TestSession()
    db.add_all([
        Incident(camera_id=1, event_type="old verified", confidence=0.9,
                 status=IncidentStatus.VERIFIED, timestamp=old),
        Incident(camera_id=1, event_type="old open", confidence=0.9,
                 status=IncidentStatus.OPEN, timestamp=old),
        Incident(camera_id=1, event_type="fresh verified", confidence=0.9,
                 status=IncidentStatus.VERIFIED),
    ])
    db.commit()
    db.close()

    removed = retention.purge_expired(days=30)
    assert removed == 1
    db = TestSession()
    remaining = {i.event_type for i in db.query(Incident).all()}
    db.close()
    assert remaining == {"old open", "fresh verified"}


def test_retention_zero_days_is_noop():
    from app.core import retention
    assert retention.purge_expired(days=0) == 0


def test_incident_confidence_is_validated():
    with pytest.raises(ValidationError):
        IncidentCreate(camera_id=1, event_type="x", confidence=2.5)


def test_short_password_rejected():
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", name="A", password="short")


def test_auth_gate_enforced_when_required(monkeypatch):
    from fastapi.testclient import TestClient
    import main

    main.Base.metadata.create_all(bind=main.engine)
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    client = TestClient(main.app)
    # Reads and writes alike require a token now — no open endpoints.
    assert client.get("/api/cameras/").status_code == 401
    assert client.post("/api/cameras/", json={"name": "c", "location_id": 1}).status_code == 401


def test_auth_gate_closed_even_when_flag_off(monkeypatch):
    """AUTH_REQUIRED=false no longer disables authentication (fail-closed).

    The flag is retained for old .env files but has no effect: an anonymous
    mutation must 401 regardless of the flag.
    """
    from fastapi.testclient import TestClient
    import main

    main.Base.metadata.create_all(bind=main.engine)
    monkeypatch.setattr(settings, "AUTH_REQUIRED", False)
    client = TestClient(main.app)
    # Business logic would 400 on the missing location — the 401 proves the
    # auth gate fired first.
    assert client.post("/api/cameras/", json={"name": "c", "location_id": 999}).status_code == 401
    assert client.get("/api/cameras/").status_code == 401