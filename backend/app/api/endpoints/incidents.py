from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models import Incident, Camera
from ...schemas import IncidentResponse, IncidentCreate, IncidentUpdate, IncidentDetail
from ...core.bus import bus
from ..deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Incident).order_by(Incident.timestamp.desc()).all()

@router.get("/active", response_model=List[IncidentResponse])
def get_active_incidents(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    from ...models import IncidentStatus
    return db.query(Incident).filter(Incident.status == IncidentStatus.OPEN).order_by(Incident.timestamp.desc()).all()

@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@router.post("/", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    cam = db.query(Camera).filter(Camera.id == incident.camera_id).first()
    if cam is None:
        raise HTTPException(status_code=400, detail="camera_id does not exist")
    db_inc = Incident(**incident.model_dump())
    db.add(db_inc)
    db.commit()
    db.refresh(db_inc)
    return db_inc

@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, patch: IncidentUpdate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = patch.status
    db.commit()
    db.refresh(inc)
    bus.broadcast_sync({"type": "incident_updated", "id": inc.id, "status": patch.status.value})
    return inc
