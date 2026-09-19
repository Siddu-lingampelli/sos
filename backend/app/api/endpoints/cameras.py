from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models import Camera
from ...schemas import CameraResponse, CameraCreate

router = APIRouter()

@router.get("/", response_model=List[CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()

@router.post("/", response_model=CameraResponse)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    db_cam = Camera(**camera.model_dump())
    db.add(db_cam)
    db.commit()
    db.refresh(db_cam)
    return db_cam
