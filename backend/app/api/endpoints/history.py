"""Incident history (Level 2.6 /api/history).

A read-only, paginated, filterable view over resolved incidents. Kept
separate from /api/incidents so the dashboard's history table can page
through months of data without loading every row into memory.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from ...db.session import get_db
from ...models import Incident, IncidentStatus, Camera, Location
from ...schemas import IncidentResponse
from ..deps import require_auth

router = APIRouter()


def _parse_since(since: Optional[str]):
    """Strict ISO parsing: a malformed `since` is a 422, not a silently
    unfiltered query an operator could mistake for a reviewed time window."""
    if not since:
        return None
    from datetime import datetime
    try:
        return datetime.fromisoformat(since)
    except ValueError:
        raise HTTPException(status_code=422, detail="since must be ISO date/datetime, e.g. 2026-01-01")


@router.get("/", response_model=List[IncidentResponse], dependencies=[Depends(require_auth)])
def get_history(
    db: Session = Depends(get_db),
    status: Optional[IncidentStatus] = Query(default=None),
    location_id: Optional[int] = Query(default=None, ge=1),
    camera_id: Optional[int] = Query(default=None, ge=1),
    since: Optional[str] = Query(default=None, description="ISO date, e.g. 2026-01-01"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    q = db.query(Incident)
    if status is not None:
        q = q.filter(Incident.status == status)
    if camera_id is not None:
        q = q.filter(Incident.camera_id == camera_id)
    if location_id is not None:
        q = q.join(Camera, Incident.camera_id == Camera.id).filter(Camera.location_id == location_id)
    dt = _parse_since(since)
    if dt is not None:
        q = q.filter(Incident.timestamp >= dt)
    return (q.order_by(Incident.timestamp.desc())
              .offset(offset)
              .limit(limit)
              .all())


@router.get("/count", dependencies=[Depends(require_auth)])
def get_history_count(
    db: Session = Depends(get_db),
    status: Optional[IncidentStatus] = Query(default=None),
    location_id: Optional[int] = Query(default=None, ge=1),
    camera_id: Optional[int] = Query(default=None, ge=1),
    since: Optional[str] = Query(default=None, description="ISO date, e.g. 2026-01-01"),
):
    # Same filters as get_history so a paginated UI never disagrees with the count.
    q = db.query(func.count(Incident.id))
    if status is not None:
        q = q.filter(Incident.status == status)
    if camera_id is not None:
        q = q.filter(Incident.camera_id == camera_id)
    if location_id is not None:
        q = q.join(Camera, Incident.camera_id == Camera.id).filter(Camera.location_id == location_id)
    dt = _parse_since(since)
    if dt is not None:
        q = q.filter(Incident.timestamp >= dt)
    return {"count": q.scalar() or 0}
