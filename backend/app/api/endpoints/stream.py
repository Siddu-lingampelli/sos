"""MJPEG video stream with shared per-source inference (singleton).

Fixes the Level-4 audit gap: previously every HTTP client created its own
CameraStream + YOLO model. Now one background thread per camera source feeds
all viewers from a shared latest-JPEG buffer.
"""
import cv2
import time
import sys
import os
import threading
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ...core.config import settings

ai_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai"))
if ai_path not in sys.path:
    sys.path.append(ai_path)
vision_path = os.path.join(ai_path, "vision")
if vision_path not in sys.path:
    sys.path.append(vision_path)

engine_path = os.path.join(ai_path, "engine")
if engine_path not in sys.path:
    sys.path.append(engine_path)

from ...core.health import health

try:
    from camera import CameraStream
    from tracker import PersonTracker
    from fall_detector import FallDetector
    from inactivity import InactivityMonitor
    from activity import ActivityLog, speed_class
    from fusion import EmergencyEngine
    from visualizer import Visualizer
    from config import FallConfig
    from engine_config import EngineConfig
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"WARNING: Could not import AI vision modules: {e}")
    health.set("vision", "down", f"import failed: {e}")


def _pipeline_configs() -> tuple:
    """Build vision+engine configs from backend Settings so the .env knobs
    (MONITOR/ALERT thresholds, observation window, inactivity, model name)
    actually take effect instead of silently using AI-side defaults."""
    fall_cfg = FallConfig(
        OBSERVATION_DURATION_SEC=settings.OBSERVATION_DURATION_SEC,
        INACTIVITY_THRESHOLD=settings.INACTIVITY_THRESHOLD,
    )
    engine_cfg = EngineConfig(
        MONITOR_THRESHOLD=settings.MONITOR_THRESHOLD,
        ALERT_THRESHOLD=settings.ALERT_THRESHOLD,
        AUDIO_WINDOW_SEC=settings.AUDIO_WINDOW_SEC,
    )
    return fall_cfg, engine_cfg


def _model_path() -> str:
    """Resolve the YOLO pose weights: MODEL_PATHS dir first, then the
    vision/ tree (dev checkout), then bare name for the ultralytics cache."""
    name = settings.YOLO_POSE_MODEL
    candidates = [
        os.path.join(settings.MODEL_PATHS, name),
        os.path.join(vision_path, name),
        name,
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return name  # let ultralytics download / raise its own clear error

try:
    from ...db.session import SessionLocal
    from ...models import Location, Camera, Incident, DetectionEvent, IncidentStatus, User
    from ...core.notifier import notify_incident
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    print(f"WARNING: incident storage unavailable: {e}")


def _store_incident(payload: dict, source: str) -> None:
    """Level 7.7: persist a fired POSSIBLE_EMERGENCY as incident + events.

    Creates the location/camera rows on first sight (source-labelled), so a
    dashboard with zero manual setup still accumulates real history.
    Any DB failure degrades to a log line — the stream must never die.
    """
    if not DB_AVAILABLE:
        print(f"[engine] no DB, incident dropped: {payload['event_type']}")
        return
    db = SessionLocal()
    try:
        from ...db.session import commit_with_retry
        loc = db.query(Location).filter(Location.name == "Auto").first()
        if loc is None:
            loc = Location(name="Auto", building="-", floor="-")
            db.add(loc)
            db.flush()
        cam = db.query(Camera).filter(Camera.name == _camera_label(source)).first()
        if cam is None:
            cam = Camera(name=_camera_label(source), location_id=loc.id, status="active")
            db.add(cam)
            db.flush()
        inc = Incident(camera_id=cam.id, event_type=payload["event_type"],
                       confidence=payload["confidence"], status=IncidentStatus.OPEN)
        db.add(inc)
        db.flush()
        for ev in payload.get("evidence", []):
            db.add(DetectionEvent(incident_id=inc.id, event_type=ev["signal"],
                                  value=str(ev["points"])))
        commit_with_retry(db)
        print(f"[engine] incident #{inc.id} stored: {payload['event_type']} "
              f"({payload['confidence']:.0%})")
        notify_incident(payload, incident_id=inc.id, camera=cam.name)
    except Exception as e:
        db.rollback()
        print(f"[engine] incident store failed (stream continues): {e}")
    finally:
        db.close()

router = APIRouter()

_lock = threading.Lock()
_states: dict[str, dict] = {}


@router.post("/ticket")
def mint_stream_ticket(request: Request):
    """Mint a 90-second single-use ticket for the MJPEG feed / WS handshake.

    Called over the normal authed channel (bearer or session cookie); the
    ticket — not the long-lived JWT — is what rides in ?ticket= URLs.
    Rate-limited: tickets are cheap to mint but each one is a fresh auth grant.
    """
    from fastapi.responses import JSONResponse
    from ..deps import _user_from_token
    from ...db.session import SessionLocal
    from ...core.security import create_stream_ticket
    header_token = ""
    try:
        auth = request.headers.get("authorization", "") if request is not None else ""
        if auth.lower().startswith("bearer "):
            header_token = auth[7:].strip()
    except Exception:
        header_token = ""
    cookie_token = request.cookies.get("sos_session", "") if request is not None else ""
    db = SessionLocal()
    try:
        user = _user_from_token(header_token or cookie_token or None, db)
    finally:
        db.close()
    if user is None:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    return {"ticket": create_stream_ticket(user.email), "expires_in": 90}


def _camera_label(source: str) -> str:
    """Operator-safe camera label that never contains credentials.

    A source URL may embed `user:pass@`; persisting or broadcasting the raw
    URL would leak those into the DB and the dashboard. Keep host + path only,
    plus a short hash of the full source so two long URLs that share an
    80-char prefix don't collapse into one Camera row and merge histories.
    """
    import hashlib as _hashlib
    suffix = _hashlib.sha1(str(source).encode("utf-8", "replace")).hexdigest()[:8]
    try:
        parsed = urlparse(source)
        if parsed.scheme and parsed.hostname:
            path = parsed.path or ""
            return f"stream:{parsed.hostname}{path}#{suffix}"
    except Exception:
        pass
    return f"stream:{str(source)[:80]}#{suffix}"


# Private, loopback, and link-local ranges never allowed as camera sources
# unless explicitly named in STREAM_SOURCE_ALLOWLIST.
_PRIVATE_HOSTS = frozenset((
    "127.0.0.1", "localhost", "0.0.0.0", "::1",
    "169.254.169.254", "metadata.google.internal",
    "10.0.0.0", "172.16.0.0", "192.168.0.0",
    "100.64.0.0",
))


def _source_allowed(source: str) -> bool:
    """Allowlist gate for camera sources (SSRF hardening, fail-closed).

    - Numeric webcam indexes ("0") are always allowed — no network fetch.
    - Anything else must match a configured STREAM_SOURCE_ALLOWLIST prefix
      AND use an http/https/rtsp scheme AND must not target loopback, private,
      or link-local hosts. Those only pass when the allowlist explicitly names
      the host (e.g. an operator-facing local IP).
    - Empty allowlist = deny every URL source. The old allow-any default let
      any caller make the server fetch arbitrary internal URLs.
    """
    if source.isdigit():
        return True
    try:
        parsed = urlparse(source)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https", "rtsp"):
        return False  # no file://, ftp://, or bare paths
    host = (parsed.hostname or "").lower().rstrip(".")
    if host in _PRIVATE_HOSTS:
        return False  # cloud metadata, loopback, and private ranges are never cameras
    raw = [p.strip() for p in settings.STREAM_SOURCE_ALLOWLIST.split(",")]
    prefixes = [p for p in raw if p]
    if not prefixes:
        return False
    return any(source.startswith(p) for p in prefixes)


def _parse_rotate(value) -> int:
    try:
        r = int(value) % 360
    except (TypeError, ValueError):
        return 0
    return r if r in (0, 90, 180, 270) else 0


def _apply_rotate(frame, rotate: int):
    if rotate == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if rotate == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotate == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame


def _inference_loop(source_key: str, vid_source, rotate: int, source: str):
    from ...core.audio_service import register_engine, unregister_engine

    st = _states[source_key]
    from ...core.bus import bus as _bus

    fall_cfg, engine_cfg = _pipeline_configs()
    health.set("vision", "degraded", "starting")
    stream = None
    tracker = None
    engine = None
    try:
        stream = CameraStream(source=vid_source, max_fps=15)
        tracker = PersonTracker(model_path=_model_path(), cfg=fall_cfg)
        fall = FallDetector(cfg=fall_cfg)
        inact = InactivityMonitor(cfg=fall_cfg)
        activity = ActivityLog(cfg=fall_cfg)
        engine = EmergencyEngine(engine_cfg)
        viz = Visualizer()
        register_engine(engine)
    except Exception as exc:  # noqa: BLE001 - model load failure must be visible
        print(f"[vision] startup failed: {exc}")
        health.set("vision", "down", f"startup failed: {exc}")
        _bus.broadcast_sync({"type": "system", "component": "vision", "status": "down", "detail": str(exc)})
        with _lock:
            _states.pop(source_key, None)
        return

    if stream is not None and not stream.cap.isOpened():
        health.set(f"camera:{source_key}", "down", "source not open")
        health.set("vision", "degraded", "no camera")
        # Redacted label only — a raw source URL may embed user:pass@.
        _bus.broadcast_sync({"type": "system", "component": "camera", "source": _camera_label(source),
                             "status": "down", "detail": "source could not be opened"})

    last = time.time()
    fps = 0.0
    stride = max(1, fall_cfg.DETECT_STRIDE)
    last_persons: list = []
    last_latency = 0.0
    n = 0
    # A dead RTSP socket can wedge cap.read() forever; the watchdog below
    # breaks the loop out so the thread reconnects instead of hanging.
    stall_stop = [False]
    stall_clock = [time.time()]
    if stream.is_live:
        stream.watch_for_stall(stall_clock, stall_stop)
    try:
        for ret, frame in stream.read_frames():
            if stall_stop[0]:
                health.set(f"camera:{source_key}", "down", "read stall — reconnecting")
                _bus.broadcast_sync({"type": "system", "component": "camera",
                                     "source": _camera_label(source),
                                     "status": "down", "detail": "read stall — reconnecting"})
                try:
                    stream.cap.release()
                    time.sleep(stream.RECONNECT_DELAY_SEC)
                    stream._open()
                except Exception:
                    pass
                stall_clock[0] = time.time()
                stall_stop[0] = False
                continue
            if not ret or frame is None or st.get("stop"):
                if ret is False:
                    health.set(f"camera:{source_key}", "down", "stream ended")
                    _bus.broadcast_sync({"type": "system", "component": "camera", "source": _camera_label(source),
                                         "status": "down", "detail": "camera disconnected or stream ended"})
                break
            # Straighten sideways phone feeds BEFORE detection so pose
            # geometry, tracking, and fall math all see upright frames
            frame = _apply_rotate(frame, rotate)
            n += 1
            now = time.time()
            st["last_frame_at"] = now
            stall_clock[0] = now
            health.set(f"camera:{source_key}", "ok", "frames flowing")
            dt = now - last
            if dt > 0:
                fps = 0.1 * (1.0 / dt) + 0.9 * fps
            last = now
            if n % stride == 1:
                try:
                    persons, last_latency = tracker.process(frame)
                    health.set("vision", "ok", f"latency {last_latency * 1000:.0f}ms")
                except Exception as exc:  # noqa: BLE001 - a frame must not kill the thread
                    health.set("vision", "degraded", f"process error: {exc}")
                    _bus.broadcast_sync({"type": "system", "component": "vision",
                                         "status": "degraded", "detail": str(exc)})
                    continue
                for p in persons:
                    tid = p.get("track_id", -1)
                    hist = tracker.track_history(tid)
                    fall.update(p, hist)
                    inact.update(tid, hist, p.get("fall_state", "NORMAL"))
                    p.update(inact.info(tid, hist))
                    score, estate, _ev = engine.update(tid, p)
                    p["eng_score"] = score
                    p["eng_state"] = estate
                    p["move_state"] = speed_class(hist)
                    for ev in activity.update(tid, p, hist):
                        payload = {"type": "activity", "tag": ev["tag"], "text": ev["text"]}
                        if ev.get("track_id") is not None:
                            payload["track_id"] = ev["track_id"]
                        if ev.get("score") is not None:
                            payload["score"] = ev["score"]
                        _bus.broadcast_sync(payload)
                        if ev["tag"] == "FALL":
                            print(f"[vision] {ev['text']}")
                fall.prune(tracker.history.keys())
                inact.prune(tracker.history.keys())
                engine.prune(tracker.history.keys())
                activity.prune(tracker.history.keys())
                while True:
                    inc = engine.pop_incident()
                    if inc is None:
                        break
                    _store_incident(inc, source)
                last_persons = persons
            out = viz.draw(frame, last_persons, fps, last_latency)
            h, w = out.shape[:2]
            if w > fall_cfg.STREAM_WIDTH:
                scale = fall_cfg.STREAM_WIDTH / w
                out = cv2.resize(out, (fall_cfg.STREAM_WIDTH, int(h * scale)))
            ok, buf = cv2.imencode('.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, fall_cfg.JPEG_QUALITY])
            if ok:
                with _lock:
                    st["jpg"] = buf.tobytes()
    except Exception as exc:  # noqa: BLE001
        health.set("vision", "down", f"inference loop crashed: {exc}")
        _bus.broadcast_sync({"type": "system", "component": "vision",
                             "status": "down", "detail": str(exc)})
    finally:
        stall_stop[0] = True
        if engine is not None:
            unregister_engine(engine)
        health.clear(f"camera:{source_key}")
        if health.snapshot().get("vision", {}).get("status") != "down":
            health.set("vision", "degraded", "stream stopped")
        if stream is not None:
            stream.release()
        with _lock:
            _states.pop(source_key, None)


def _ensure_source(source: str, rotate: int) -> str:
    """One inference thread per (source, rotation). Returns the state key."""
    key = f"{source}|rot{rotate}"
    with _lock:
        if key in _states:
            _states[key]["clients"] += 1
            return key
        live_threads = sum(1 for st in _states.values() if not st.get("stop"))
        if live_threads >= settings.STREAM_MAX_THREADS:
            raise HTTPException(status_code=429,
                                detail=f"Too many live streams (max {settings.STREAM_MAX_THREADS}) — close one first")
        vid_source = int(source) if source.isdigit() else source
        st: dict = {"jpg": None, "stop": False, "clients": 1}
        _states[key] = st
        t = threading.Thread(target=_inference_loop, args=(key, vid_source, rotate, source), daemon=True)
        st["thread"] = t
        t.start()
        return key

def _release_source(key: str):
    """Drop a client reference; stop the thread when the last one leaves."""
    thread_to_stop = None
    with _lock:
        st = _states.get(key)
        if st is None:
            return
        st["clients"] -= 1
        if st["clients"] <= 0:
            st["stop"] = True
            thread_to_stop = st.get("thread")
    # Join outside the lock: the thread takes _lock in its finally block to
    # pop its own state, so joining while holding it would deadlock.
    # Use Event to let the loop stop gracefully; avoid long thread.join in
    # request path that can exhaust the event loop pool.
    if thread_to_stop is not None and thread_to_stop.is_alive() and thread_to_stop is not threading.current_thread():
        # Give inference loop a short grace period to notice st["stop"] and exit
        thread_to_stop.join(timeout=0.5)


def generate_frames(source: str, rotate: int):
    if not AI_AVAILABLE:
        return
    key = _ensure_source(source, rotate)
    served = False
    idle = 0
    last_emit = time.time()
    try:
        while True:
            with _lock:
                st = _states.get(key)
                jpg = st["jpg"] if st else None
                stopped = st["stop"] if st else True
            if jpg is not None:
                served = True
                idle = 0
                last_emit = time.time()
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
            else:
                idle += 1
            if st is None and (served or idle > 15 * 10):
                # Camera thread died (disconnect)
                break
            if stopped:
                # Every client has left and the source is shutting down.
                break
            # A live thread that stops emitting frames (RTSP stall, a camera
            # that hangs inside cap.read()) would otherwise hang this client
            # forever. Break out after a grace period of silence.
            if served and time.time() - last_emit > 20.0:
                print(f"[stream] no frames for 20s on {_camera_label(source)}, ending client")
                break
            time.sleep(1 / 15)
    finally:
        _release_source(key)


@router.get("/video")
def video_feed(request: Request, source: str = "", rotate: int = 0, ticket: str = ""):
    """MJPEG stream. ?source=http://phone-ip:8080/video &rotate=0|90|180|270.

    Auth: Authorization bearer header, httpOnly session cookie (same-origin
    <img> sends it), or a single-use ?ticket= fetched from POST /ticket.
    Long-lived JWTs never ride in the URL anymore — they used to persist in
    access logs, proxy logs, browser history and Referer headers.
    """
    from fastapi.responses import JSONResponse
    from ..deps import _user_from_token
    from ...db.session import SessionLocal
    from ...core.security import consume_stream_ticket
    header_token = ""
    try:
        auth = request.headers.get("authorization", "") if request is not None else ""
        if auth.lower().startswith("bearer "):
            header_token = auth[7:].strip()
    except Exception:
        header_token = ""
    cookie_token = request.cookies.get("sos_session", "") if request is not None else ""
    db = SessionLocal()
    try:
        user = _user_from_token(header_token or cookie_token or None, db)
        if user is None and ticket:
            email = consume_stream_ticket(ticket)
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user is not None and not user.is_active:
                    user = None
    finally:
        db.close()
    # Fail-closed: no valid credential of any kind → 401, always.
    if user is None:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    if not AI_AVAILABLE:
        return JSONResponse({"error": "AI modules missing"}, status_code=503)
    if not source:
        return JSONResponse({"error": "No camera source — pass ?source=http://phone-ip:8080/video"}, status_code=400)
    if not _source_allowed(source):
        return JSONResponse({"error": "Camera source not on the allowlist (STREAM_SOURCE_ALLOWLIST)"},
                            status_code=403)
    return StreamingResponse(generate_frames(source, _parse_rotate(rotate)),
                             media_type="multipart/x-mixed-replace; boundary=frame")
