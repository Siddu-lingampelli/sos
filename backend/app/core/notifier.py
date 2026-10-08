"""Notification fan-out (Level 9).

An incident can leave the system through two channels:
  websocket -> already handled by AlertBus in stream.py
  email     -> optional SMTP, only when SMTP_HOST is configured

Every attempted delivery is recorded as an Alert row so the operator can see
whether a channel actually fired. A notification failure must never kill the
inference thread, so every path degrades to a log line.
"""
import smtplib
import threading
from email.message import EmailMessage

from .bus import bus


def _smtp_enabled() -> bool:
    from .config import settings
    return bool(getattr(settings, "SMTP_HOST", ""))


def _send_email(subject: str, body: str) -> tuple[bool, str]:
    from .config import settings
    if not settings.SMTP_HOST:
        return False, "smtp not configured"
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.ALERT_FROM or settings.SMTP_USER
    msg["To"] = settings.ALERT_TO
    msg.set_content(body)
    try:
        if settings.SMTP_PORT == 465:
            # Implicit TLS (SMTPS) — STARTTLS on 465 always fails.
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as srv:
                if settings.SMTP_USER:
                    srv.login(settings.SMTP_USER, settings.SMTP_PASS)
                srv.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as srv:
                try:
                    srv.starttls()
                except smtplib.SMTPException:
                    pass  # plaintext relay — continue without TLS
                if settings.SMTP_USER:
                    srv.login(settings.SMTP_USER, settings.SMTP_PASS)
                srv.send_message(msg)
        return True, "sent"
    except Exception as exc:  # noqa: BLE001 - delivery must never bubble up
        return False, f"email failed: {exc}"


def _record_alert(incident_id: int | None, channel: str, status: str) -> None:
    try:
        from ..db.session import SessionLocal, commit_with_retry
        from ..models import Alert
        db = SessionLocal()
        try:
            db.add(Alert(incident_id=incident_id, channel=channel, status=status))
            commit_with_retry(db)
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] alert row skipped: {exc}")


def _format_body(payload: dict) -> str:
    evidence = ", ".join(
        f"{e.get('signal')}={e.get('points')}" for e in payload.get("evidence", [])
    )
    return (
        "SilentSOS possible emergency\n\n"
        f"Type: {payload.get('event_type', 'Possible emergency')}\n"
        f"Confidence: {payload.get('confidence', 0):.0%}\n"
        f"Track: {payload.get('track_id')}\n"
        f"Evidence: {evidence or 'n/a'}\n\n"
        "Human verification required."
    )


def notify_incident(payload: dict, incident_id: int | None = None, camera: str | None = None) -> None:
    """Fan out an incident to the dashboard and optional email.

    Runs in the inference thread; email is dispatched on a short-lived daemon
    thread so a slow SMTP server cannot stall video processing.
    """
    conf = payload.get("confidence", 0.0)
    event_type = payload.get("event_type", "Possible emergency")
    bus.broadcast_sync({
        # "notification" is the delivery message; "incident" (no id) is the
        # separate message a manual POST /incidents sends. Keeping the types
        # distinct lets the dashboard tell an AI-filed incident from an
        # operator-created one.
        "type": "notification",
        "id": incident_id,
        "camera": camera or "?",
        "event_type": event_type,
        "confidence": conf,
        "status": "OPEN",
        "channel": "websocket",
        "track_id": payload.get("track_id"),
    })
    _record_alert(incident_id, "websocket", "sent")

    if not _smtp_enabled():
        return

    def _worker() -> None:
        ok, status = _send_email(
            f"[SilentSOS] {event_type}", _format_body(payload)
        )
        _record_alert(incident_id, "email", status if ok else status)
        print(f"[notify] email {status}")

    threading.Thread(target=_worker, daemon=True).start()