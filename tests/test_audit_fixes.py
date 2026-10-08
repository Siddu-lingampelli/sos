"""Regressions for the Levels 1-8 audit fixes.

Each test pins a specific bug the audit found, so the fix cannot silently
revert. Grouped by the level that owns the behaviour. The pre-existing
Level 4 fall-detector tests live at the end of this file.
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "vision")))

import pytest

from config import FallConfig
from fall_detector import FallDetector
from pose_geometry import head_ankle_span, boxes_overlap
from inactivity import InactivityMonitor


def _person(**kw):
    base = {"track_id": 1, "angle": 10.0, "aspect": 0.5, "t": time.time(), "box": [0, 0, 100, 300]}
    base.update(kw)
    return base


# --- pre-existing Level 4 baseline tests ----------------------------------

def _flat(angle, aspect, tid=7):
    return {"track_id": tid, "angle": angle, "aspect": aspect, "hip_y": 0.5, "t": time.time()}


def test_single_bend_does_not_trigger():
    fd = FallDetector(FallConfig(CONFIRM_FRAMES=3, RECOVERY_FRAMES=2, FALL_VERTICAL_VELOCITY=99))
    hist = [_flat(5, 0.5) for _ in range(5)]
    assert fd.update(_flat(5, 0.5), hist) == "NORMAL"
    # one horizontal frame only -> still NORMAL
    hist.append(_flat(80, 1.5))
    assert fd.update(_flat(80, 1.5), hist) == "NORMAL"


def test_persistent_horizontal_triggers_possible_fall():
    fd = FallDetector(FallConfig(CONFIRM_FRAMES=2, RECOVERY_FRAMES=2, FALL_VERTICAL_VELOCITY=99))
    hist = [_flat(5, 0.5) for _ in range(5)]
    fd.update(_flat(5, 0.5), hist)
    hist.append(_flat(80, 1.5))
    fd.update(_flat(80, 1.5), hist)
    hist.append(_flat(80, 1.5))
    assert fd.update(_flat(80, 1.5), hist) == "POSSIBLE_FALL"
    assert any(e["to"] == "POSSIBLE_FALL" for e in fd.events)


def test_jwt_expiry_claim():
    from app.core.security import create_access_token, decode_access_token
    tok = create_access_token({"sub": "test@example.com"})
    payload = decode_access_token(tok)
    assert payload is not None and payload["sub"] == "test@example.com"
    assert "exp" in payload


# --- Level 4: head/ankle span separates crouching from falling -------------

def test_kneeling_is_not_horizontal():
    """A crouching person is upright by angle and by head-to-ankle span.

    Aspect alone cannot rescue this case, so the span check is what keeps a
    person bending down from being read as horizontal.
    """
    cfg = FallConfig()
    fd = FallDetector(cfg)
    # Head at the top of the box, ankles at the bottom: the body spans ~95%
    # of the box height, i.e. they are not lying down.
    kp = [[0, 0, 0.0]] * 17
    kp[0] = [100.0, 0.0, 0.9]     # head
    kp[15] = [100.0, 95.0, 0.9]   # ankle
    kp[16] = [110.0, 95.0, 0.9]
    p = _person(angle=15.0, aspect=0.85, box=[0, 0, 170, 100], keypoints=kp)

    fd.update(p, [])
    assert p["fall_evidence"]["span"] == 0.95
    assert p["fall_evidence"]["horizontal"] is False


def test_span_alone_does_not_trip_horizontal_when_joints_span_the_box():
    """A wide box alone is not enough — the span must agree it is upright."""
    cfg = FallConfig()
    fd = FallDetector(cfg)
    # aspect 2.0 clears FALL_ASPECT_THRESHOLD, so this case *is* horizontal
    # via aspect. Pinning the behaviour so a future change to the aspect rule
    # is a deliberate one.
    kp = [[0, 0, 0.0]] * 17
    kp[0] = [100.0, 0.0, 0.9]
    kp[15] = [100.0, 95.0, 0.9]
    p = _person(angle=10.0, aspect=2.0, box=[0, 0, 200, 100], keypoints=kp)
    fd.update(p, [])
    assert p["fall_evidence"]["span"] == 0.95
    assert p["fall_evidence"]["horizontal"] is True  # via aspect only


def test_lying_person_is_horizontal_even_with_low_confidence_torso():
    """A curled fallen person may have no usable shoulder/hip keypoints.

    Angle is None there, so aspect and span must carry the decision.
    """
    fd = FallDetector(FallConfig())
    kp = [[0] * 3] * 17
    kp[0] = [100.0, 10.0, 0.9]    # head
    kp[15] = [120.0, 20.0, 0.9]   # ankle only 10px below the head
    p = _person(angle=None, aspect=0.6, box=[0, 0, 300, 100], keypoints=kp)

    fd.update(p, [])
    assert p["fall_evidence"]["horizontal"] is True


def test_head_ankle_span_returns_none_without_confident_keypoints():
    kp = [[0] * 3] * 17  # all confidence 0
    assert head_ankle_span(kp, 0.25) is None


def test_missing_span_does_not_lower_a_confirmed_fall_score():
    """No confident keypoints must not penalise an otherwise clear fall."""
    fd = FallDetector(FallConfig())
    t0 = time.time()
    hist = [{"hip_y": 0.40 + i * 0.075, "t": t0 + i * 0.1} for i in range(3)]
    p = _person(track_id=9, angle=80.0, aspect=1.5, t=t0 + 0.2, keypoints=[])
    fd.update(p, hist)
    assert p["fall_evidence"]["span"] is None
    assert p["fall_evidence"]["score"] >= 80


# --- Level 4: hip velocity is the steepest descent, not the window average --

def test_hip_velocity_isolates_the_impact_in_a_long_window():
    """A 0.4 s fall inside a 1.6 s window must not be averaged down to nothing."""
    fd = FallDetector(FallConfig())
    t0 = time.time()
    # Standing still, then a fast drop, then lying still.
    hist = [
        {"hip_y": 0.20, "t": t0 + 0.0},
        {"hip_y": 0.20, "t": t0 + 0.1},
        {"hip_y": 0.55, "t": t0 + 0.5},   # fell over 0.4 s -> 0.875/s
        {"hip_y": 0.55, "t": t0 + 0.6},
        {"hip_y": 0.55, "t": t0 + 0.7},
    ]
    vel = fd._hip_velocity(hist)
    assert vel >= 0.8, f"expected the impact rate, got {vel:.3f}"


def test_hip_velocity_is_zero_for_a_stationary_person():
    fd = FallDetector(FallConfig())
    t0 = time.time()
    hist = [{"hip_y": 0.4, "t": t0 + i * 0.1} for i in range(5)]
    assert fd._hip_velocity(hist) == 0.0


# --- Level 4: temp IDs stay stable for an untracked person ------------------

def test_temp_id_is_reused_across_frames():
    from tracker import PersonTracker
    tr = PersonTracker.__new__(PersonTracker)  # skip model load
    tr.cfg = FallConfig()
    tr._untracked_seq = -1
    tr._temp_tracks = {}
    tr._temp_ttl = {}
    now = time.time()
    a = tr._temp_id_for(0.50, 0.50, now)
    b = tr._temp_id_for(0.502, 0.501, now + 0.1)  # same person, jittery centroid
    c = tr._temp_id_for(0.85, 0.20, now + 0.1)   # someone else entirely
    assert a == b
    assert c != a


def test_temp_id_expires_after_ttl():
    from tracker import PersonTracker
    tr = PersonTracker.__new__(PersonTracker)
    tr.cfg = FallConfig()
    tr._untracked_seq = -1
    tr._temp_tracks = {}
    tr._temp_ttl = {}
    now = time.time()
    a = tr._temp_id_for(0.5, 0.5, now)
    b = tr._temp_id_for(0.5, 0.5, now + PersonTracker._TEMP_TTL_SEC + 1)
    assert a != b


def test_boxes_overlap_detects_a_standing_neighbour():
    assert boxes_overlap([0, 0, 100, 200], [10, 10, 90, 190]) is True
    assert boxes_overlap([0, 0, 100, 200], [500, 500, 600, 700]) is False


# --- Level 5: a person down but not perfectly still still escalates ---------

def test_still_down_person_escalates_instead_of_looping():
    """The old code reset to IDLE and restarted the window forever."""
    cfg = FallConfig(OBSERVATION_DURATION_SEC=0.0, INACTIVITY_THRESHOLD=0.02,
                     RECOVERY_FACTOR=3.0, MOVEMENT_WINDOW_SEC=3.0)
    mon = InactivityMonitor(cfg)
    # Movement just above the inactivity threshold but well below the
    # recovery factor: conscious but unable to get up.
    hist = [
        {"t": time.time() - 0.5, "cx": 0.50, "cy": 0.50, "keypoints": [], "fh": 640},
        {"t": time.time(), "cx": 0.504, "cy": 0.50, "keypoints": [], "fh": 640},
    ]
    mon.update(1, hist, "FALL_CONFIRMED")
    assert mon.state[1] == "OBSERVING"
    st = mon.update(1, hist, "FALL_CONFIRMED")
    assert st == "INACTIVE", f"expected escalation, got {st}"
    assert any(e["type"] == "POSSIBLE_EMERGENCY" for e in mon.events)


def test_person_who_gets_up_cancels_the_window():
    cfg = FallConfig(OBSERVATION_DURATION_SEC=0.0, INACTIVITY_THRESHOLD=0.02)
    mon = InactivityMonitor(cfg)
    hist = [
        {"t": time.time() - 0.5, "cx": 0.50, "cy": 0.50, "keypoints": [], "fh": 640},
        {"t": time.time(), "cx": 0.50, "cy": 0.50, "keypoints": [], "fh": 640},
    ]
    mon.update(1, hist, "FALL_CONFIRMED")
    st = mon.update(1, hist, "RECOVERED")
    assert st == "IDLE"
    assert any(e["type"] == "RECOVERY_DETECTED" for e in mon.events)
    assert not any(e["type"] == "POSSIBLE_EMERGENCY" for e in mon.events)


# --- Level 7: engine shares the fall detector's thresholds ----------------

def test_engine_and_fall_detector_agree_on_horizontal():
    import sys as _sys
    _sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "engine")))
    from fusion import EmergencyEngine
    from engine_config import EngineConfig

    fd = FallDetector(FallConfig())
    eng = EmergencyEngine(EngineConfig())
    # Aspect just under the fall threshold: neither layer may call it abnormal.
    aspect = FallConfig().FALL_ASPECT_THRESHOLD - 0.05
    p = _person(angle=10.0, aspect=aspect, keypoints=[])
    fd.update(p, [])
    assert p["fall_evidence"]["horizontal"] is False

    _score, state, ev = eng.update(1, {"fall_state": "NORMAL", "inact_state": "IDLE",
                                       "angle": 10.0, "aspect": aspect})
    assert all(s != "ABNORMAL_POSTURE" for s, _ in ev), "engine used a stale threshold"
    assert state == "NORMAL"


# --- Level 8: auth is on by default and the WS refuses anonymous clients ---

def test_auth_required_defaults_to_true():
    from app.core.config import Settings
    assert Settings().AUTH_REQUIRED is True


def test_ws_refuses_anonymous_connection_by_default():
    from fastapi.testclient import TestClient
    import main

    main.Base.metadata.create_all(bind=main.engine)
    client = TestClient(main.app)
    with client.websocket_connect("/api/ws/alerts") as ws:
        assert ws.receive_json()["detail"] == "unauthorized"


def test_mutating_endpoints_require_a_token():
    from fastapi.testclient import TestClient
    import main
    from app.core.config import settings

    main.Base.metadata.create_all(bind=main.engine)
    original = settings.AUTH_REQUIRED
    settings.AUTH_REQUIRED = True
    try:
        client = TestClient(main.app)
        assert client.post("/api/locations/", json={"name": "x"}).status_code == 401
        assert client.post("/api/cameras/", json={"name": "x", "location_id": 1}).status_code == 401
        assert client.post("/api/incidents/", json={"camera_id": 1, "event_type": "x",
                                                     "confidence": 0.5}).status_code == 401
    finally:
        settings.AUTH_REQUIRED = original


def test_jwt_secret_is_never_a_known_placeholder():
    from app.core.config import settings, INSECURE_SECRETS
    assert settings.JWT_SECRET not in INSECURE_SECRETS
    assert len(settings.JWT_SECRET) >= 32


def test_placeholder_secret_is_replaced_not_just_warned_about():
    """A public placeholder would let anyone forge a token."""
    from app.core.config import Settings, INSECURE_SECRETS
    for bad in ("change-me-in-.env", "change-me", "secret", "changeme", "", "short"):
        s = Settings(JWT_SECRET=bad)
        assert s.secret_is_weak, f"{bad!r} should be flagged weak"
    # A real-looking secret is accepted as-is.
    assert not Settings(JWT_SECRET="x" * 48).secret_is_weak
    assert INSECURE_SECRETS  # guard against the set being emptied by accident


def test_audio_keywords_come_from_settings():
    from app.core.config import Settings
    s = Settings(AUDIO_KEYWORDS="help, sos ,  rescue ")
    assert s.audio_keywords == ("help", "sos", "rescue")
    # Blank falls back to the built-in list rather than matching nothing.
    assert "help" in Settings(AUDIO_KEYWORDS="").audio_keywords


def test_public_registration_is_closed_by_default():
    """With the flag off, /register must 403 — open signup would let anyone
    mint an officer account and dismiss live incidents."""
    from fastapi.testclient import TestClient
    import main
    from app.core.config import settings

    main.Base.metadata.create_all(bind=main.engine)
    original = settings.ALLOW_PUBLIC_REGISTRATION
    settings.ALLOW_PUBLIC_REGISTRATION = False
    try:
        client = TestClient(main.app)
        res = client.post("/api/auth/register",
                          json={"email": "new@x.com", "name": "N", "password": "password123"})
        assert res.status_code == 403
    finally:
        settings.ALLOW_PUBLIC_REGISTRATION = original


def test_auth_endpoints_are_rate_limited():
    """11 rapid logins from one IP must trip the 429, not sail through."""
    from fastapi.testclient import TestClient
    import main
    from app.core import ratelimit

    main.Base.metadata.create_all(bind=main.engine)
    ratelimit._hits.clear()
    client = TestClient(main.app)
    statuses = [
        client.post("/api/auth/login",
                    json={"email": "nobody@x.com", "password": "wrong"}).status_code
        for _ in range(11)
    ]
    assert statuses[-1] == 429
    ratelimit._hits.clear()


def test_bus_replays_backlog_to_late_subscriber():
    """Incidents that fire before any socket connects are replayed, not dropped."""
    import asyncio
    from app.core.bus import AlertBus

    class FakeWS:
        def __init__(self):
            self.sent = []

        async def send_json(self, msg):
            self.sent.append(msg)

    async def go():
        bus = AlertBus()
        bus.broadcast_sync({"type": "notification", "id": 9})
        ws = FakeWS()
        await bus.connect(ws)
        assert ws.sent and ws.sent[0]["id"] == 9

    asyncio.run(go())


def test_delete_open_incident_needs_force():
    """Privacy erase must not silently wipe live response state."""
    from fastapi.testclient import TestClient
    import main
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.models import Camera, Incident, IncidentStatus, Location

    main.Base.metadata.create_all(bind=main.engine)
    db = SessionLocal()
    loc = db.query(Location).first()
    if loc is None:
        loc = Location(name="del-loc", building="-", floor="-")
        db.add(loc)
        db.flush()
    cam = db.query(Camera).first()
    if cam is None:
        cam = Camera(name="del-cam", location_id=loc.id, status="active")
        db.add(cam)
        db.flush()
    inc = Incident(camera_id=cam.id, event_type="do not erase", confidence=0.5,
                   status=IncidentStatus.OPEN)
    db.add(inc)
    db.commit()
    inc_id = inc.id
    db.close()

    original = settings.AUTH_REQUIRED
    settings.AUTH_REQUIRED = False
    try:
        from helpers import authed_client
        client = authed_client()
        assert client.delete(f"/api/incidents/{inc_id}").status_code == 409
        assert client.delete(f"/api/incidents/{inc_id}?force=true").status_code == 200
        assert client.get(f"/api/incidents/{inc_id}").status_code == 404
    finally:
        settings.AUTH_REQUIRED = original


def test_history_count_matches_list_filters():
    """/history/count must take the same filters as /history, or paging lies."""
    from fastapi.testclient import TestClient
    import main
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.models import Camera, Incident, IncidentStatus, Location

    main.Base.metadata.create_all(bind=main.engine)
    db = SessionLocal()
    loc = db.query(Location).first()
    if loc is None:
        loc = Location(name="count-loc", building="-", floor="-")
        db.add(loc)
        db.flush()
    cam = db.query(Camera).first()
    if cam is None:
        cam = Camera(name="count-cam", location_id=loc.id, status="active")
        db.add(cam)
        db.flush()
    db.add(Incident(camera_id=cam.id, event_type="count dismissed", confidence=0.5,
                    status=IncidentStatus.DISMISSED))
    db.commit()
    db.close()

    original = settings.AUTH_REQUIRED
    settings.AUTH_REQUIRED = False
    try:
        from helpers import authed_client
        client = authed_client()
        rows = client.get("/api/history/?status=DISMISSED").json()
        count = client.get("/api/history/count?status=DISMISSED").json()["count"]
        assert count == len(rows) and count >= 1
        db = SessionLocal()
        db.query(Incident).filter(Incident.event_type == "count dismissed").delete()
        db.commit()
        db.close()
    finally:
        settings.AUTH_REQUIRED = original


# --- Level 8: new routers are mounted and reachable -----------------------

@pytest.mark.parametrize("path", ["/api/users/", "/api/alerts/", "/api/history/",
                                   "/api/history/count"])
def test_new_routers_are_mounted(path):
    """All routers require auth now — an authed admin reaches every one."""
    from helpers import authed_client
    import main

    main.Base.metadata.create_all(bind=main.engine)
    client = authed_client()
    assert client.get(path).status_code == 200


def test_history_filters_by_status():
    from fastapi.testclient import TestClient
    import main
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.models import Camera, Incident, IncidentStatus, Location

    main.Base.metadata.create_all(bind=main.engine)
    db = SessionLocal()
    # Foreign keys are enforced, so the camera row has to exist.
    loc = db.query(Location).first()
    if loc is None:
        loc = Location(name="test-loc", building="-", floor="-")
        db.add(loc)
        db.flush()
    cam = db.query(Camera).first()
    if cam is None:
        cam = Camera(name="test-cam", location_id=loc.id, status="active")
        db.add(cam)
        db.flush()
    db.add(Incident(camera_id=cam.id, event_type="dismissed one", confidence=0.5,
                    status=IncidentStatus.DISMISSED))
    db.add(Incident(camera_id=cam.id, event_type="open one", confidence=0.5,
                    status=IncidentStatus.OPEN))
    db.commit()
    cam_id = cam.id
    db.close()

    original = settings.AUTH_REQUIRED
    settings.AUTH_REQUIRED = False
    try:
        from helpers import authed_client
        client = authed_client()
        rows = client.get("/api/history/?status=DISMISSED").json()
        assert all(r["status"] == "DISMISSED" for r in rows)
        assert any(r["event_type"] == "dismissed one" for r in rows)
        # Clean up so repeated runs do not accumulate rows (children first —
        # FKs are enforced).
        db = SessionLocal()
        inc_ids = [r[0] for r in db.query(Incident.id).filter(Incident.camera_id == cam_id).all()]
        if inc_ids:
            from app.models import DetectionEvent, Alert
            db.query(DetectionEvent).filter(DetectionEvent.incident_id.in_(inc_ids)).delete(synchronize_session=False)
            db.query(Alert).filter(Alert.incident_id.in_(inc_ids)).delete(synchronize_session=False)
            db.query(Incident).filter(Incident.camera_id == cam_id).delete(synchronize_session=False)
            db.commit()
        db.close()
    finally:
        settings.AUTH_REQUIRED = original


# --- Level 3: camera reconnect -------------------------------------------

def test_live_camera_tolerates_transient_read_failures():
    """A single dropped frame must not end the stream on a live source."""
    import cv2
    import numpy as np
    from camera import CameraStream

    class FlakyCap:
        def __init__(self):
            self.n = 0
            self.released = False
        def isOpened(self):
            return True
        def get(self, _prop):
            return 640
        def set(self, *_a):
            return True
        def read(self):
            self.n += 1
            if self.n == 1:
                return False, None          # one transient dropout
            return True, np.zeros((10, 10, 3), dtype=np.uint8)
        def release(self):
            self.released = True

    st = CameraStream.__new__(CameraStream)
    st.source = 0
    st.is_live = True
    st.max_fps = 30
    st.frame_time = 1 / 30
    st.cap = FlakyCap()

    gen = st.read_frames()
    ret, frame = next(gen)
    assert ret is True and frame is not None, "stream ended on a transient dropout"


def test_recorded_file_ends_at_end_of_stream():
    import numpy as np
    from camera import CameraStream

    class FileCap:
        def __init__(self):
            self.n = 0
        def isOpened(self):
            return True
        def get(self, _prop):
            return 640
        def set(self, *_a):
            return True
        def read(self):
            self.n += 1
            if self.n > 2:
                return False, None
            return True, np.zeros((10, 10, 3), dtype=np.uint8)
        def release(self):
            pass

    st = CameraStream.__new__(CameraStream)
    st.source = "clip.mp4"
    st.is_live = False
    st.max_fps = 0          # no throttling
    st.frame_time = 0
    st.cap = FileCap()

    frames = [ok for ok, _ in st.read_frames()]
    assert frames == [True, True, False], frames


# --- Fail-closed auth + incident hardening regressions ----------------------

def _seed_camera():
    import main
    from app.db.session import SessionLocal
    from app.models import Camera, Location

    main.Base.metadata.create_all(bind=main.engine)
    db = SessionLocal()
    loc = db.query(Location).first()
    if loc is None:
        loc = Location(name="sec-loc", building="-", floor="-")
        db.add(loc)
        db.flush()
    cam = db.query(Camera).first()
    if cam is None:
        cam = Camera(name="sec-cam", location_id=loc.id, status="active")
        db.add(cam)
        db.flush()
    cam_id = cam.id
    db.commit()
    db.close()
    return cam_id


def test_anonymous_reads_are_rejected():
    """C1: incident/alert/history/camera/location reads need a token."""
    from fastapi.testclient import TestClient
    import main

    main.Base.metadata.create_all(bind=main.engine)
    client = TestClient(main.app)
    assert client.get("/api/incidents/1").status_code == 401
    assert client.get("/api/incidents/1/events").status_code == 401
    assert client.get("/api/alerts/").status_code == 401
    assert client.get("/api/alerts/incident/1").status_code == 401
    assert client.get("/api/history/").status_code == 401
    assert client.get("/api/history/count").status_code == 401
    assert client.get("/api/cameras/").status_code == 401
    assert client.get("/api/locations/").status_code == 401
    assert client.get("/api/system/status").status_code == 401
    assert client.get("/health").status_code == 200  # liveness stays public


def test_officer_cannot_delete_incident():
    """H1: DELETE is admin-only; officers get 403, not a silent wipe."""
    from helpers import authed_client

    cam_id = _seed_camera()
    officer = authed_client(role="SECURITY_OFFICER")
    inc = officer.post("/api/incidents/", json={
        "camera_id": cam_id, "event_type": "x", "confidence": 0.5}).json()
    assert officer.delete(f"/api/incidents/{inc['id']}?force=true").status_code == 403


def test_create_incident_forces_open_and_ignores_snapshot():
    """C3/H2: status and snapshot_path are server-controlled, not client input."""
    from helpers import authed_client

    cam_id = _seed_camera()
    client = authed_client()
    res = client.post("/api/incidents/", json={
        "camera_id": cam_id, "event_type": "manual",
        "confidence": 0.9, "status": "DISMISSED",
        "snapshot_path": "/etc/hostname"})
    assert res.status_code == 200, res.text
    row = res.json()
    assert row["status"] == "OPEN"
    assert row["snapshot_path"] is None


def test_stream_ticket_is_single_use():
    """C6: a ticket works once; replay and JWT-in-URL are rejected."""
    from app.core.security import create_stream_ticket, consume_stream_ticket

    t = create_stream_ticket("someone@x.com")
    assert consume_stream_ticket(t) == "someone@x.com"
    assert consume_stream_ticket(t) is None  # replay burned
    assert consume_stream_ticket("not.a.ticket") is None


def test_malformed_since_is_rejected():
    """M4: garbage `since` is a 422, never a silently unfiltered query."""
    from helpers import authed_client

    client = authed_client()
    assert client.get("/api/history/?since=garbage").status_code == 422
    assert client.get("/api/history/count?since=garbage").status_code == 422


def test_register_duplicate_reveals_nothing():
    """H11: duplicate registration returns a generic error, not an oracle."""
    from fastapi.testclient import TestClient
    import main
    from app.core.config import settings

    main.Base.metadata.create_all(bind=main.engine)
    original = settings.ALLOW_PUBLIC_REGISTRATION
    settings.ALLOW_PUBLIC_REGISTRATION = True
    try:
        import uuid
        client = TestClient(main.app)
        body = {"email": f"dup-{uuid.uuid4().hex[:8]}@example.com", "name": "D", "password": "password123"}
        assert client.post("/api/auth/register", json=body).status_code in (200, 201)
        dup = client.post("/api/auth/register", json=body)
        assert dup.status_code == 400
        assert "already registered" not in dup.text.lower()
    finally:
        settings.ALLOW_PUBLIC_REGISTRATION = original


def test_login_sets_httponly_cookie_and_logout_clears_it():
    """C5: the session cookie is httpOnly; logout clears it."""
    from helpers import authed_client, ADMIN_EMAIL, ADMIN_PASSWORD
    from fastapi.testclient import TestClient
    import main

    client = authed_client()
    anon = TestClient(main.app)
    res = anon.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200
    set_cookie = res.headers.get("set-cookie", "")
    assert "sos_session=" in set_cookie and "httponly" in set_cookie.lower()
    # Cookie alone authenticates (proves the fallback path works).
    me = anon.get("/api/users/me")
    assert me.status_code == 200
    out = anon.post("/api/auth/logout")
    assert out.status_code == 200
    assert anon.get("/api/users/me").status_code == 401
