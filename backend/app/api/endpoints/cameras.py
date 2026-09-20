from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models import Camera, Location
from ...schemas import CameraResponse, CameraCreate
from ..deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[CameraResponse])
def get_cameras(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Camera).all()

@router.post("/", response_model=CameraResponse)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    loc = db.query(Location).filter(Location.id == camera.location_id).first()
    if loc is None:
        raise HTTPException(status_code=400, detail="location_id does not exist")
    db_cam = Camera(**camera.model_dump())
    db.add(db_cam)
    db.commit()
    db.refresh(db_cam)
    return db_cam
