from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models import Incident, Camera
from ...schemas import IncidentResponse, IncidentCreate
from ..deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Incident).all()

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
