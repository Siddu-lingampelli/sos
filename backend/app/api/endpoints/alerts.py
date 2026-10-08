"""Alert delivery history (Level 2.6 /api/alerts).

Every notification attempt the notifier makes writes an Alert row, so this
endpoint is how an operator answers "did the dashboard/email actually go out?"
rather than assuming a successful send from the absence of an error.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ...db.session import get_db
from ...models import Alert, Incident
from ...schemas import IncidentResponse
from ..deps import require_auth

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    incident_id: int
    channel: str
    status: str
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertWithIncident(BaseModel):
    """An alert joined to enough incident context to render a row."""
    id: int
    channel: str
    status: str
    sent_at: datetime
    incident: IncidentResponse

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[AlertWithIncident], dependencies=[Depends(require_auth)])
def get_alerts(
    db: Session = Depends(get_db),
    channel: Optional[str] = Query(default=None, max_length=40),
    since: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
):
    q = (db.query(Alert).join(Alert.incident)
           .options(joinedload(Alert.incident)))
    if channel:
        q = q.filter(Alert.channel == channel)
    if since:
        # Delivery time is the one clock this endpoint filters on. (An older
        # version OR'd in the incident time, which mixed two clocks and
        # returned rows a dashboard could not page consistently.)
        q = q.filter(Alert.sent_at >= since)
    rows = q.order_by(Alert.sent_at.desc()).limit(limit).all()
    return [{"id": a.id, "channel": a.channel, "status": a.status,
             "sent_at": a.sent_at, "incident": a.incident} for a in rows if a.incident]


@router.get("/incident/{incident_id}", response_model=List[AlertResponse], dependencies=[Depends(require_auth)])
def get_incident_alerts(incident_id: int, db: Session = Depends(get_db)):
    """Delivery attempts for one incident, newest first."""
    if db.query(Incident).filter(Incident.id == incident_id).first() is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return (db.query(Alert)
            .filter(Alert.incident_id == incident_id)
            .order_by(Alert.sent_at.desc())
            .all())
