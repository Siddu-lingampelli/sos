"""App config — reads .env, falls back to Level-1 defaults."""
import secrets
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict

# Known placeholder secrets. Any of these is public knowledge, so a token
# signed with one could be forged by anyone; they are replaced at import.
INSECURE_SECRETS = {
    "change-me-in-.env",
    "change-me",
    "secret",
    "changeme",
    "",
}


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./silentsos.db"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    # 2h sessions: a stolen incident-dismissal token must not live for half a day.
    JWT_EXPIRE_MINUTES: int = 120
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Trust X-Forwarded-For for rate-limit client IPs only when an actual
    # reverse proxy strips/spoofs it. Off by default: behind no proxy the
    # header is attacker-controlled and would let anyone rotate identities.
    TRUST_PROXY: bool = False
    # httpOnly session cookie set at login. Secure requires HTTPS — keep off
    # for localhost dev, turn on the moment TLS terminates in front.
    SESSION_COOKIE_SECURE: bool = False

    # Auth is always enforced: there is no anonymous mode. AUTH_REQUIRED is
    # retained so old .env files still parse, but it no longer disables
    # authentication — an unauthenticated deployment lets anyone dismiss real
    # emergency incidents.
    AUTH_REQUIRED: bool = True
    SEED_ADMIN_EMAIL: str = ""
    SEED_ADMIN_PASSWORD: str = ""
    RETENTION_DAYS: int = 30
    # Public self-registration. Off by default: with it on, anyone who can
    # reach the API can mint an officer account and then dismiss live
    # emergency incidents. Admins create accounts via /api/users/ instead.
    ALLOW_PUBLIC_REGISTRATION: bool = False

    # AI thresholds (mirror ai/vision/config.py + ai/engine/engine_config.py
    # defaults; the backend builds its configs from these so .env tuning
    # actually takes effect — see stream.py / audio_service.py).
    MONITOR_THRESHOLD: float = 40.0
    ALERT_THRESHOLD: float = 70.0
    OBSERVATION_DURATION_SEC: float = 10.0
    INACTIVITY_THRESHOLD: float = 0.02
    # Seconds an audio distress event stays fused into the score. Short on
    # purpose: a 30 s-old shout must not stack onto fresh vision evidence.
    AUDIO_WINDOW_SEC: float = 10.0
    YOLO_POSE_MODEL: str = "yolo11n-pose.pt"
    MODEL_PATHS: str = "./models"
    WHISPER_MODEL_SIZE: str = "tiny"

    # Stream hardening (see api/endpoints/stream.py).
    STREAM_MAX_THREADS: int = 4
    # Comma-separated allowed source prefixes, e.g.
    # "rtsp://cam1,http://192.168.1.". Empty = deny every URL source (webcam
    # indexes still work) — fail-closed, because an allow-any backend fetches
    # attacker URLs with server credentials (SSRF).
    STREAM_SOURCE_ALLOWLIST: str = ""
    # Server-controlled directory for incident snapshot files. DELETE only
    # ever removes files inside it — never a client-supplied path.
    SNAPSHOT_DIR: str = "./snapshots"

    # Optional email notifications
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    ALERT_FROM: str = ""
    ALERT_TO: str = ""

    # Level 6 — comma-separated distress keywords, overrides the built-in list
    AUDIO_KEYWORDS: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if not origins:  # fall back to localhost when CORS_ORIGINS env is empty (Docker / prod must set this explicitly)
            origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
        return origins

    @property
    def audio_keywords(self) -> tuple[str, ...]:
        raw = [k.strip().lower() for k in self.AUDIO_KEYWORDS.split(",")]
        return tuple(k for k in raw if k) or DEFAULT_KEYWORDS

    @property
    def secret_is_weak(self) -> bool:
        return self.JWT_SECRET.strip() in INSECURE_SECRETS or len(self.JWT_SECRET) < 32


DEFAULT_KEYWORDS = ("help", "emergency", "please help", "someone help")

settings = Settings()

# The signing algorithm is not negotiable at runtime: accepting a configured
# "none" (or an asymmetric alg against an HMAC secret) would let anyone mint
# tokens. Refuse to boot instead of running with a forged-token hole.
if settings.JWT_ALGORITHM != "HS256":
    raise RuntimeError(
        f"JWT_ALGORITHM={settings.JWT_ALGORITHM!r} is not allowed — this service "
        "only signs and verifies HS256."
    )

# A publicly documented example password must never silently protect a real
# database: copying .env.example verbatim would hand the DB to everyone.
try:
    from urllib.parse import urlparse, unquote
    from os import getenv as _getenv

    _pg_passwords = {
        _getenv("POSTGRES_PASSWORD", ""),
        unquote(urlparse(settings.DATABASE_URL).password or ""),
    }
    if settings.DATABASE_URL.startswith("postgres") and _pg_passwords & INSECURE_SECRETS:
        warnings.warn(
            "POSTGRES_PASSWORD is empty or a publicly known placeholder — "
            "generate a real one; .env.example values are public knowledge.",
            RuntimeWarning,
            stacklevel=1,
        )
except Exception:
    pass

# A placeholder secret is worse than none: it is public knowledge, so anyone
# could mint a token that validates. Replace any weak/placeholder value with a
# random per-process key and warn loudly, so the service is never protected by
# a secret the README already published. The key changes on restart, so set a
# real JWT_SECRET for anything that must survive one.
if settings.secret_is_weak:
    warnings.warn(
        "JWT_SECRET is unset or a known placeholder — replacing it with a "
        "process-local random key. Tokens will not survive a restart, and you "
        "must sign in again. Generate a real one with:\n"
        '  python -c "import secrets; print(secrets.token_urlsafe(48))"',
        RuntimeWarning,
        stacklevel=1,
    )
    settings.JWT_SECRET = secrets.token_urlsafe(48)
