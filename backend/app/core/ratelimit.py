"""Sliding-window rate limiters (process-local).

Login/register without throttling invite credential stuffing; the stream, ticket
and mutation paths need their own budgets because each burns real resources (a
YOLO thread, a fresh auth grant, a DB write). Process-local state is fine here —
a restart only resets counters, and multi-replica deployments should terminate
TLS/rate-limit at the reverse proxy anyway.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from .config import settings

WINDOW_SEC = 60.0
MAX_HITS = 10

_hits: dict[str, deque[float]] = defaultdict(deque)
_last_sweep = 0.0


def _client_ip(request: Request) -> str:
    if settings.TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def _sweep(now: float) -> None:
    """Evict idle keys so the per-IP map cannot grow without bound."""
    global _last_sweep
    if now - _last_sweep < WINDOW_SEC:
        return
    _last_sweep = now
    for key in [k for k, dq in _hits.items() if not dq or now - dq[-1] > WINDOW_SEC]:
        _hits.pop(key, None)


def _check(key: str, max_hits: int = MAX_HITS, window: float = WINDOW_SEC) -> None:
    now = time.time()
    _sweep(now)
    dq = _hits[key]
    while dq and now - dq[0] > window:
        dq.popleft()
    if len(dq) >= max_hits:
        raise HTTPException(status_code=429, detail="Too many attempts — try again in a minute")
    dq.append(now)


def login_rate_limit(request: Request) -> None:
    """FastAPI dependency: throttle brute-forceable auth routes per client IP."""
    _check(f"auth:{_client_ip(request)}")


def api_rate_limit(request: Request) -> None:
    """General budget for authed read/write routes: 120/min/IP."""
    _check(f"api:{_client_ip(request)}", max_hits=120)


def stream_rate_limit(request: Request) -> None:
    """MJPEG and socket-adjacent paths spawn threads: 15 new viewers/min/IP."""
    _check(f"stream:{_client_ip(request)}", max_hits=15)


def ticket_rate_limit(request: Request) -> None:
    """Ticket minting is a fresh auth grant each time: 30/min/IP."""
    _check(f"ticket:{_client_ip(request)}", max_hits=30)


def ws_rate_limit(request: Request) -> None:
    """Handshake attempts (reconnect storms): 20/min/IP."""
    _check(f"ws:{_client_ip(request)}", max_hits=20)
