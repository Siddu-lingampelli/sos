from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db, commit_with_retry
from ...models import Camera, Location
from ...schemas import CameraResponse, CameraCreate
from ..deps import require_auth, require_admin

router = APIRouter()

@router.get("/", response_model=List[CameraResponse], dependencies=[Depends(require_auth)])
def get_cameras(db: Session = Depends(get_db),
                limit: int = Query(default=500, ge=1, le=500)):
    return db.query(Camera).order_by(Camera.id).limit(limit).all()

@router.post("/", response_model=CameraResponse, dependencies=[Depends(require_admin)])
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == camera.location_id).first()
    if loc is None:
        raise HTTPException(status_code=400, detail="location_id does not exist")
    db_cam = Camera(**camera.model_dump())
    db.add(db_cam)
    commit_with_retry(db)
    db.refresh(db_cam)
    return db_cam
