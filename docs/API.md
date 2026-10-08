# API

Base URL: `http://localhost:8000`. Auth: bearer JWT or httpOnly session cookie.
Authentication is always enforced (fail-closed) — every endpoint except `/`,
`/health` and the auth routes requires a valid token; there is no anonymous
mode and `AUTH_REQUIRED=false` does not disable auth.

## Auth

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/auth/register` | creates a SECURITY_OFFICER (only when `ALLOW_PUBLIC_REGISTRATION=true`) |
| POST | `/api/auth/login` | returns `{access_token, token_type}` + sets httpOnly `sos_session` cookie |
| POST | `/api/auth/logout` | clears the session cookie (auth required) |

## Locations / Cameras

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/locations/` | auth required |
| POST | `/api/locations/` | auth required, ADMIN only |
| GET | `/api/cameras/` | auth required |
| POST | `/api/cameras/` | auth required, ADMIN only |

## Incidents

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/incidents/` | auth required; newest first, `?limit=` (max 200) `&offset=` |
| GET | `/api/incidents/active` | auth required; OPEN only |
| GET | `/api/incidents/{id}` | auth required; detail with detection events |
| GET | `/api/incidents/{id}/events` | auth required; event timeline, oldest first |
| POST | `/api/incidents/` | auth required; status forced OPEN, snapshot server-assigned |
| PATCH | `/api/incidents/{id}` | auth required; `{status}`; broadcasts update |
| DELETE | `/api/incidents/{id}` | ADMIN only; privacy erase; OPEN needs `?force=true` |

## Streaming

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/stream/ticket` | auth required; mints a 90 s single-use ticket |
| GET | `/api/stream/video?source=…&rotate=0\|90\|180\|270&ticket=<ticket>` | MJPEG feed (bearer/cookie, or single-use ticket — JWTs never ride in URLs) |
| WS | `/api/ws/alerts` | incident/notification/activity/system events; `?ticket=<ticket>` or session cookie |

The WebSocket refuses anonymous handshakes with
`{"type":"error","detail":"unauthorized"}` and closes 1008. Camera `source`
URLs must match `STREAM_SOURCE_ALLOWLIST` (empty = deny all URLs; webcam
indexes always allowed).
WS message types:

| Type | Emitted when |
| --- | --- |
| `connected` | handshake accepted |
| `error` | unauthorized handshake |
| `ping` | server heartbeat every ~25 s — reply with any frame |
| `notification` | the AI engine filed an incident (`id` set) |
| `incident` | an operator created one via `POST /api/incidents/` |
| `incident_updated` | status PATCH applied |
| `incident_deleted` | incident erased |
| `activity` | live narration line (walking, fall, audio event) |
| `system` | component health change (vision/audio/camera/database) |

The bus keeps a 50-message backlog: incidents that fire before any socket
connects are replayed to the next subscriber instead of being dropped.

## Users (admin)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/users/` | list accounts; admin only |
| GET | `/api/users/me` | current user |
| POST | `/api/users/` | create officer; admin only |
| PATCH | `/api/users/{id}/role?role=ADMIN\|SECURITY_OFFICER` | admin only |
| PATCH | `/api/users/{id}/active?is_active=true\|false` | admin only; cannot disable yourself |

## Alerts (delivery log)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/alerts/?channel=…&since=…&limit=…` | delivery attempts joined to incidents |
| GET | `/api/alerts/incident/{id}` | attempts for one incident |

## History

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/history/?status=…&location_id=…&camera_id=…&since=…&limit=…&offset=…` | paginated, filterable |
| GET | `/api/history/count?status=…&location_id=…&camera_id=…&since=…` | row count for the same filters |

## Health

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | liveness + overall component state |
| GET | `/api/health` | DB check + component detail |
| GET | `/api/system/status` | dashboard poll endpoint |