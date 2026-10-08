"""User management (Level 2.6 /api/users).

Listing every account is admin-only because it exposes who can respond to an
incident. Self-service profile reads are allowed for any authenticated user so
the dashboard can show "who am I" without an admin round trip.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ...db.session import get_db, commit_with_retry
from ...models import User, RoleEnum
from ...schemas import UserResponse, UserCreate
from ...core.security import get_password_hash
from ..deps import require_auth, require_admin

router = APIRouter()


@router.get("/", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
def get_users(db: Session = Depends(get_db),
              limit: int = Query(default=500, ge=1, le=500)):
    return db.query(User).order_by(User.id).limit(limit).all()


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Who am I — the dashboard's identity check. Always authenticated."""
    row = db.query(User).filter(User.id == user.id).first()
    if row is None:
        # Token valid at decode time but the account vanished since.
        raise HTTPException(status_code=404, detail="Account not found")
    return row


@router.post("/", response_model=UserResponse, status_code=201,
             dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Admin creates an officer account with a specific role."""
    if db.query(User).filter(User.email == payload.email).first():
        # Same generic message as public registration — no oracle either way.
        raise HTTPException(status_code=400, detail="Could not complete registration for this email")
    new_user = User(
        email=payload.email,
        name=payload.name,
        password_hash=get_password_hash(payload.password),
        role=RoleEnum.SECURITY_OFFICER,
    )
    db.add(new_user)
    commit_with_retry(db)
    db.refresh(new_user)
    return new_user


@router.patch("/{user_id}/role", response_model=UserResponse,
              dependencies=[Depends(require_admin)])
def set_role(user_id: int, role: RoleEnum, db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = role
    commit_with_retry(db)
    db.refresh(target)
    return target


@router.patch("/{user_id}/active", response_model=UserResponse,
              dependencies=[Depends(require_admin)])
def set_active(user_id: int, is_active: bool, db: Session = Depends(get_db),
               admin: User = Depends(require_admin)):
    """Enable or disable an account. Admins cannot disable themselves."""
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    target.is_active = is_active
    commit_with_retry(db)
    db.refresh(target)
    return target
