from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from ...db.session import get_db, commit_with_retry
from ...models import Incident, Camera, DetectionEvent, Alert, IncidentStatus
from ...schemas import IncidentResponse, IncidentCreate, IncidentUpdate, IncidentDetail, DetectionEventResponse
from ...core.bus import bus
from ...core.notifier import notify_incident
from ..deps import require_auth, require_admin
from ...core.retention import remove_snapshot_file

router = APIRouter()

@router.get("/", response_model=List[IncidentResponse], dependencies=[Depends(require_auth)])
def get_incidents(db: Session = Depends(get_db),
                  limit: int = Query(default=100, ge=1, le=200),
                  offset: int = Query(default=0, ge=0)):
    return (db.query(Incident).order_by(Incident.timestamp.desc())
            .offset(offset).limit(limit).all())

@router.get("/active", response_model=List[IncidentResponse], dependencies=[Depends(require_auth)])
def get_active_incidents(db: Session = Depends(get_db),
                         limit: int = Query(default=100, ge=1, le=200)):
    return (db.query(Incident).filter(Incident.status == IncidentStatus.OPEN)
            .order_by(Incident.timestamp.desc()).limit(limit).all())

@router.get("/{incident_id}", response_model=IncidentDetail, dependencies=[Depends(require_auth)])
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = (db.query(Incident).options(joinedload(Incident.events))
           .filter(Incident.id == incident_id).first())
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.get("/{incident_id}/events", response_model=List[DetectionEventResponse], dependencies=[Depends(require_auth)])
def get_incident_events(incident_id: int, db: Session = Depends(get_db)):
    """Event history for the dossier timeline."""
    if db.query(Incident.id).filter(Incident.id == incident_id).first() is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return (db.query(DetectionEvent).filter(DetectionEvent.incident_id == incident_id)
            .order_by(DetectionEvent.timestamp.asc()).all())

@router.post("/", response_model=IncidentResponse, dependencies=[Depends(require_auth)])
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == incident.camera_id).first()
    if cam is None:
        raise HTTPException(status_code=400, detail="camera_id does not exist")
    db_inc = Incident(camera_id=incident.camera_id, event_type=incident.event_type,
                      confidence=incident.confidence, status=IncidentStatus.OPEN)
    db.add(db_inc)
    commit_with_retry(db)
    db.refresh(db_inc)
    notify_incident({
        "event_type": db_inc.event_type,
        "confidence": db_inc.confidence,
        "evidence": [],
    }, incident_id=db_inc.id, camera=cam.name)
    return db_inc

@router.patch("/{incident_id}", response_model=IncidentResponse, dependencies=[Depends(require_auth)])
def update_incident(incident_id: int, patch: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    # IDOR mitigation: verify user is active and authorized; incidents are
    # public-read but mutations require auth; optional ownership logic could go here
    inc.status = patch.status
    commit_with_retry(db)
    db.refresh(inc)
    bus.broadcast_sync({"type": "incident_updated", "id": inc.id, "status": patch.status.value})
    return inc

@router.delete("/{incident_id}", dependencies=[Depends(require_admin)])
def delete_incident(incident_id: int, db: Session = Depends(get_db),
                    force: bool = Query(default=False, description="Also erase OPEN incidents")):
    """Privacy control: erase a resolved incident and its event history.

    OPEN incidents are protected — erasing live response state needs force=true.
    Snapshot files on disk are removed alongside the DB rows, and only when
    they live inside the server-controlled snapshot directory.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if inc.status == IncidentStatus.OPEN and not force:
        raise HTTPException(status_code=409,
                            detail="Incident is still OPEN — resolve it first or pass force=true")
    snapshot = inc.snapshot_path
    db.query(DetectionEvent).filter(DetectionEvent.incident_id == incident_id).delete()
    db.query(Alert).filter(Alert.incident_id == incident_id).delete()
    db.delete(inc)
    commit_with_retry(db)
    remove_snapshot_file(snapshot)
    bus.broadcast_sync({"type": "incident_deleted", "id": incident_id})
    return {"deleted": incident_id}