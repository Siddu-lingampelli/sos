from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from ...db.session import get_db, commit_with_retry
from ...models import User, RoleEnum
from ...schemas import UserCreate, UserResponse, LoginRequest, Token
from ...core.security import get_password_hash, verify_password, create_access_token
from ...core.config import settings
from ...core.ratelimit import login_rate_limit
from ..deps import SESSION_COOKIE, require_auth

router = APIRouter()

@router.post("/register", response_model=UserResponse, dependencies=[Depends(login_rate_limit)])
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """Self-service signup. Disabled unless ALLOW_PUBLIC_REGISTRATION is on —
    otherwise anyone could mint an officer account and dismiss live incidents.
    Admins create accounts via POST /api/users/ regardless of this flag."""
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Public registration is disabled — ask an admin for an account")
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        # Generic message: a distinct "already registered" error is an
        # account-enumeration oracle for credential stuffing.
        raise HTTPException(status_code=400, detail="Could not complete registration for this email")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        name=user.name,
        password_hash=hashed_password,
        role=RoleEnum.SECURITY_OFFICER
    )
    db.add(new_user)
    commit_with_retry(db)
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token, dependencies=[Depends(login_rate_limit)])
def login(request: Request, req_body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req_body.email).first()
    if not user or not verify_password(req_body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    role = getattr(user.role, "value", user.role) or RoleEnum.SECURITY_OFFICER.value
    access_token = create_access_token(data={"sub": user.email, "role": role})
    # httpOnly session cookie: JS can never read it, so XSS cannot steal it.
    # The JSON body keeps the bearer for API calls; the cookie is the fallback
    # that survives a page reload without localStorage.
    response.set_cookie(
        SESSION_COOKIE,
        access_token,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response, user: User = Depends(require_auth)):
    """Clear the session cookie. The bearer (if any) stays valid until expiry —
    short-lived by configuration — but the browser session ends here."""
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"logged_out": user.email}
