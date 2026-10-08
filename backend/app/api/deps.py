"""Auth dependencies — JWT enforced on all protected routes (fail-closed).

There is no anonymous mode: every route that takes require_auth / get_current_user
returns 401 without a valid token for an active user. An ``AUTH_REQUIRED``
env flag still exists for documentation purposes but no longer disables
authentication — an unauthenticated deployment is one where anyone can dismiss
real emergency incidents, so fail-open is never an option.
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models import User
from ..core.security import decode_access_token
from ..core.config import settings

bearer = HTTPBearer(auto_error=False)

SESSION_COOKIE = "sos_session"


def _token_from_request(
    creds: HTTPAuthorizationCredentials | None,
    request: Request | None,
) -> str | None:
    if creds and creds.credentials:
        return creds.credentials
    if request is not None:
        cookie_token = request.cookies.get(SESSION_COOKIE)
        if cookie_token:
            return cookie_token
    return None


def _user_from_token(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        return None
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Bearer header first, httpOnly session cookie second. 401 otherwise."""
    user = _user_from_token(_token_from_request(creds, request), db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return user


def require_auth(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Enforce JWT on all routes. Returns the authenticated user, else 401."""
    return get_current_user(request, creds, db)


def websocket_authorized(token: str | None) -> bool:
    from ..db.session import SessionLocal
    db = SessionLocal()
    try:
        return _user_from_token(token, db) is not None
    finally:
        db.close()

def websocket_user(token: str | None, db: Session) -> User | None:
    """Return validated user or None; used by WS endpoints that need identity."""
    return _user_from_token(token, db)


def require_admin(user: User = Depends(get_current_user)) -> User:
    role_val = getattr(user.role, "value", user.role)
    if role_val != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
