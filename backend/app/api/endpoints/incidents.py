from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models import Incident
from ...schemas import IncidentResponse, IncidentCreate

router = APIRouter()

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).all()

@router.post("/", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    db_inc = Incident(**incident.model_dump())
    db.add(db_inc)
    db.commit()
    db.refresh(db_inc)
    return db_inc
