from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db, commit_with_retry
from ...models import Location
from ...schemas import LocationResponse, LocationCreate
from ..deps import require_auth, require_admin

router = APIRouter()

@router.get("/", response_model=List[LocationResponse], dependencies=[Depends(require_auth)])
def get_locations(db: Session = Depends(get_db),
                  limit: int = Query(default=500, ge=1, le=500)):
    return db.query(Location).order_by(Location.id).limit(limit).all()

@router.post("/", response_model=LocationResponse, dependencies=[Depends(require_admin)])
def create_location(location: LocationCreate, db: Session = Depends(get_db)):
    db_loc = Location(**location.model_dump())
    db.add(db_loc)
    commit_with_retry(db)
    db.refresh(db_loc)
    return db_loc
