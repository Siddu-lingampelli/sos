"""Incident retention policy (Level 9 privacy).

Open incidents are never deleted. Resolved incidents (VERIFIED / DISMISSED)
older than RETENTION_DAYS are removed together with their detection events and
alert rows. This keeps raw event history bounded without touching the live
response queue.
"""
import os
import threading
import time
from datetime import datetime, timedelta, timezone

_retention_lock = threading.Lock()
_retention_thread: threading.Thread | None = None
_retention_stop = threading.Event()


def snapshot_dir() -> str:
    from .config import settings
    d = settings.SNAPSHOT_DIR or "./snapshots"
    os.makedirs(d, exist_ok=True)
    return os.path.abspath(d)


def remove_snapshot_file(path: str | None) -> bool:
    """Delete a snapshot file only if it lives inside SNAPSHOT_DIR.

    Snapshot paths are server-controlled, but legacy rows (or a future bug)
    could hold an absolute path elsewhere — never follow those. Returns True
    when a file was removed.
    """
    if not path:
        return False
    try:
        base = snapshot_dir()
        target = os.path.abspath(path)
        if os.path.commonpath([base, target]) != base:
            print(f"[retention] refusing to delete outside snapshot dir: {path}")
            return False
        if os.path.isfile(target):
            os.remove(target)
            return True
    except OSError as exc:
        print(f"[retention] snapshot delete skipped ({path}): {exc}")
    except ValueError:
        return False
    return False


def purge_expired(days: int | None = None) -> int:
    """Purge resolved incidents older than RETENTION_DAYS.

    Snapshot files are only deleted AFTER the DB commit succeeds, so a rolled
    back transaction can never leave orphaned rows or deleted files behind.
    """
    from ..db.session import SessionLocal, commit_with_retry
    from ..models import Incident, DetectionEvent, Alert, IncidentStatus
    from .config import settings

    days = settings.RETENTION_DAYS if days is None else days
    if days <= 0:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    db = SessionLocal()
    removed = 0
    paths: list = []
    try:
        stale_ids = [
            row[0] for row in (
                db.query(Incident.id)
                .filter(Incident.status.in_([IncidentStatus.VERIFIED, IncidentStatus.DISMISSED]))
                .filter(Incident.timestamp < cutoff)
                .all()
            )
        ]
        for chunk_start in range(0, len(stale_ids), 100):
            chunk = stale_ids[chunk_start:chunk_start + 100]
            paths.extend(
                row[0] for row in (
                    db.query(Incident.snapshot_path)
                    .filter(Incident.id.in_(chunk))
                    .all()
                )
            )
            db.query(DetectionEvent).filter(DetectionEvent.incident_id.in_(chunk)).delete(synchronize_session=False)
            db.query(Alert).filter(Alert.incident_id.in_(chunk)).delete(synchronize_session=False)
            db.query(Incident).filter(Incident.id.in_(chunk)).delete(synchronize_session=False)
            removed += len(chunk)
        if removed:
            commit_with_retry(db)
    except Exception as exc:
        db.rollback()
        print(f"[retention] purge failed, rolled back: {exc}")
        return 0
    finally:
        db.close()
    # Only delete files after the DB commit succeeded — never orphan rows.
    if removed:
        for p in paths:
            remove_snapshot_file(p)
    return removed


def start_retention_loop(interval_hours: int = 24) -> None:
    """Background daemon that purges expired incidents on a schedule.

    The startup call in main.py handles the first sweep; this keeps the
    retention window enforced for long-running deployments instead of once.
    """
    global _retention_thread
    with _retention_lock:
        if _retention_thread is not None and _retention_thread.is_alive():
            return
        _retention_stop.clear()
        _retention_thread = threading.Thread(
            target=_retention_loop, args=(interval_hours,), daemon=True
        )
        _retention_thread.start()


def _retention_loop(interval_hours: int) -> None:
    while not _retention_stop.wait(interval_hours * 3600):
        try:
            n = purge_expired()
            if n:
                print(f"[retention] purged {n} expired incident(s)")
        except Exception as exc:  # noqa: BLE001 - retention must never kill the loop
            print(f"[retention] purge error: {exc}")


def stop_retention_loop() -> None:
    """Signal the retention daemon to stop. Daemon threads die with the process."""
    _retention_stop.set()