from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import threading
import time

import bcrypt
import jwt

from .config import settings

# bcrypt silently truncates past 72 bytes, so two long passwords sharing a
# prefix would compare equal. Pre-hash with SHA-256 first (standard MCF
# practice), which also lifts the length cap entirely. Verification tries the
# new form first, then the legacy direct-bcrypt form so existing accounts keep
# working; new hashes are always the pre-hashed form.
_SHA256_PREFIX = "$s2b$"


def _prehash(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def get_password_hash(password: str) -> str:
    digest = _prehash(password)
    return _SHA256_PREFIX + bcrypt.hashpw(digest, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith(_SHA256_PREFIX):
            return bcrypt.checkpw(_prehash(plain_password), hashed_password[len(_SHA256_PREFIX):].encode("utf-8"))
        # Legacy direct-bcrypt hashes (pre-fix accounts).
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


# ---- Short-lived single-use stream tickets ----
# <img> and WebSocket handshakes cannot send an Authorization header, which is
# why the JWT used to ride as ?token= — landing in logs, history and Referers.
# Instead the client fetches a 90-second, single-use ticket over an authed
# channel and presents that. Theft window: ~90 s, one use, stream/WS scope only.

TICKET_TTL_SEC = 90
_TICKETS: dict[str, float] = {}
_TICKETS_LOCK = threading.Lock()


def _sweep_tickets(now: float) -> None:
    expired = [jti for jti, exp in _TICKETS.items() if exp <= now]
    for jti in expired:
        _TICKETS.pop(jti, None)


def create_stream_ticket(user_email: str) -> str:
    jti = secrets.token_urlsafe(24)
    now = time.time()
    with _TICKETS_LOCK:
        _sweep_tickets(now)
        _TICKETS[jti] = now + TICKET_TTL_SEC
    payload = {
        "sub": user_email,
        "scope": "stream",
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=TICKET_TTL_SEC),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def consume_stream_ticket(token: str) -> str | None:
    """Validate a ticket and burn it. Returns the user email, else None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("scope") != "stream" or "jti" not in payload or "sub" not in payload:
        return None
    now = time.time()
    with _TICKETS_LOCK:
        exp = _TICKETS.pop(payload["jti"], None)
        if exp is None or exp <= now:
            if exp is not None:
                _sweep_tickets(now)
            return None
    return str(payload["sub"])
