/** Shared API config + domain types. All rows come from the backend —
 *  empty means empty, never demo data. */

/** An incident's event history (fall transitions, stillness windows, audio). */
export interface ApiDetectionEvent {
  id: number;
  incident_id: number | null;
  event_type: string;
  value: string | null;
  timestamp: string;
}

/** One notification-delivery attempt for an incident. */
export interface ApiAlert {
  id: number;
  incident_id: number;
  channel: string;
  status: string;
  sent_at: string;
}

/** Alert row joined to enough incident context to render. */
export interface ApiAlertWithIncident extends ApiAlert {
  incident: ApiIncident;
}

export const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export const DEFAULT_CAMERA_SOURCE: string =
  (import.meta.env.VITE_CAMERA_SOURCE as string | undefined) ?? "";

export type IncidentStatus = "OPEN" | "UNDER_REVIEW" | "VERIFIED" | "DISMISSED";

export interface Incident {
  id: number;
  camera: string;
  location: string;
  eventType: string;
  confidence: number;
  time: string;
  status: IncidentStatus;
}

export function streamUrl(source: string, rotate = 0): Promise<string> {
  // <img> cannot send an Authorization header, so it gets a 90-second
  // single-use ticket minted over the authed API — never the long-lived JWT,
  // which used to persist in browser history, logs and Referer headers.
  return streamTicket().then((ticket) => {
    const qs = `source=${encodeURIComponent(source)}&rotate=${rotate}&ticket=${encodeURIComponent(ticket)}`;
    return `${API_URL}/api/stream/video?${qs}`;
  });
}

export function wsUrl(): Promise<string> {
  // Same ticket convention as the MJPEG feed (see streamUrl).
  let origin: string;
  try {
    origin = new URL(API_URL).origin;
  } catch {
    origin = API_URL.replace(/\/+$/, "");
  }
  const base = `${origin.replace(/^http/, "ws")}/api/ws/alerts`;
  return streamTicket().then((ticket) => `${base}?ticket=${encodeURIComponent(ticket)}`);
}

/* ---- auth session (memory token + httpOnly cookie; never localStorage) ---- */

/** Bearer for API calls. Memory-only: any XSS that could read localStorage
 *  gets nothing, and a reload re-establishes the session from the httpOnly
 *  cookie via /users/me (see ProtectedRoute). */
let memToken: string | null = null;
let authed = false;
let authVersion = 0;

export function getToken(): string | null {
  return memToken;
}

export function setToken(token: string): void {
  memToken = token;
  authed = true;
  authVersion += 1;
}

export function clearToken(): void {
  memToken = null;
  authed = false;
  authVersion += 1;
  ticketCache = null;
}

export function isAuthed(): boolean {
  return authed;
}

export function setAuthed(v: boolean): void {
  authed = v;
  authVersion += 1;
}

/** Bumps on every login/logout so sockets and guards can re-subscribe. */
export function getAuthVersion(): number {
  return authVersion;
}

/** Short-lived single-use stream ticket, cached until near-expiry. */
let ticketCache: { ticket: string; exp: number } | null = null;

export async function streamTicket(): Promise<string> {
  const now = Date.now();
  if (ticketCache && ticketCache.exp > now + 15000) return ticketCache.ticket;
  const res = await api<{ ticket: string; expires_in: number }>("/api/stream/ticket", {
    method: "POST",
  });
  ticketCache = { ticket: res.ticket, exp: now + (res.expires_in ?? 90) * 1000 };
  return res.ticket;
}

/* ---- typed API client (throws on HTTP error) ---- */

/**
 * Typed API client. Throws on HTTP error.
 *
 * A 401 means the stored token is missing, expired, or was issued with a
 * different JWT_SECRET. Bounce to the login page so a stale token cannot leave
 * the dashboard silently failing every mutation with an opaque error.
 */
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    // credentials:include carries the httpOnly session cookie, so a reload
    // restores the session without any token in JS-accessible storage.
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: { ...headers, ...(init?.headers ?? {}) },
    });
  } catch {
    // Generic message on purpose: the raw URL/path would disclose internal
    // hostnames and train operators to ignore opaque backend details.
    throw new Error("Backend unreachable — start it and retry");
  }

  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    clearToken();
    // Throttle the bounce: N failing requests must not queue N reloads.
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
    throw new Error("Session expired — redirecting to login");
  }
  if (!res.ok) {
    throw new Error(
      res.status === 404 ? "Record not found" : `Request failed (${res.status}) — retry or sign in again`,
    );
  }
  return (await res.json()) as T;
}

export interface ApiIncident {
  id: number;
  camera_id: number;
  event_type: string;
  confidence: number;
  timestamp: string;
  status: IncidentStatus;
  snapshot_path?: string | null;
}

export interface ApiCamera {
  id: number;
  name: string;
  status: string;
  location_id: number;
}

export interface ApiLocation {
  id: number;
  name: string;
  building: string;
  floor: string;
}

/** Adapt backend rows to the dashboard Incident shape. */
export async function toIncident(a: ApiIncident, cameras?: Map<number, ApiCamera>, locations?: Map<number, ApiLocation>): Promise<Incident> {
  let cameraName = `Cam #${a.camera_id}`;
  let locationName = "—";
  if (cameras) {
    const cam = cameras.get(a.camera_id);
    if (cam) {
      cameraName = cam.name;
      // Try to resolve location name via camera location_id
      if (locations && cam.location_id) {
        const loc = locations.get(cam.location_id);
        if (loc) locationName = `${loc.name} (${loc.building}/${loc.floor})`;
      }
    }
  }
  const conf = Number(a.confidence);
  const confidence = Number.isFinite(conf) ? Math.max(0, Math.min(100, Math.round(conf * 100))) : 0;
  let time = a.timestamp;
  try {
    time = new Date(a.timestamp).toLocaleString();
  } catch {
    /* keep raw */
  }
  return {
    id: a.id,
    camera: cameraName,
    location: locationName,
    eventType: a.event_type,
    confidence,
    time,
    status: a.status,
  };
}

export const AuthAPI = {
  login: (email: string, password: string) =>
    api<{ access_token: string; token_type: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, name: string, password: string) =>
    api<{ id: number; email: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, name, password }),
    }),
  me: () => api<{ id: number; email: string; is_active: boolean }>("/api/users/me"),
  logout: () => api<{ logged_out: string }>("/api/auth/logout", { method: "POST" }),
};

export interface HistoryParams {
  status?: IncidentStatus;
  location_id?: number;
  camera_id?: number;
  since?: string;
  limit?: number;
  offset?: number;
}

function historyQuery(params?: HistoryParams): string {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.location_id) q.set("location_id", String(params.location_id));
  if (params?.camera_id) q.set("camera_id", String(params.camera_id));
  if (params?.since) q.set("since", params.since);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const qs = q.toString();
  return qs ? `?${qs}` : "";
}

export const DataAPI = {
  incidents: (params?: { limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return api<ApiIncident[]>(`/api/incidents/${qs ? `?${qs}` : ""}`);
  },
  incident: (id: number) => api<ApiIncident>(`/api/incidents/${id}`),
  incidentEvents: (id: number) => api<ApiDetectionEvent[]>(`/api/incidents/${id}/events`),
  active: (limit?: number) =>
    api<ApiIncident[]>(`/api/incidents/active${limit ? `?limit=${limit}` : ""}`),
  history: (params?: HistoryParams) => api<ApiIncident[]>(`/api/history/${historyQuery(params)}`),
  historyCount: (params?: Omit<HistoryParams, "limit" | "offset">) =>
    api<{ count: number }>(`/api/history/count${historyQuery(params)}`),
  setStatus: (id: number, status: IncidentStatus) =>
    api<ApiIncident>(`/api/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  deleteIncident: (id: number, force = false) =>
    api<{ deleted: number }>(`/api/incidents/${id}${force ? "?force=true" : ""}`, {
      method: "DELETE",
    }),
  alerts: (params?: { channel?: string; since?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.channel) q.set("channel", params.channel);
    if (params?.since) q.set("since", params.since);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api<ApiAlertWithIncident[]>(`/api/alerts/${qs ? `?${qs}` : ""}`);
  },
  incidentAlerts: (id: number) => api<ApiAlert[]>(`/api/alerts/incident/${id}`),
  cameras: () => api<ApiCamera[]>("/api/cameras/"),
  locations: () => api<ApiLocation[]>("/api/locations/"),
  createLocation: (loc: { name: string; building?: string; floor?: string }) =>
    api<ApiLocation>("/api/locations/", {
      method: "POST",
      body: JSON.stringify({ name: loc.name, building: loc.building ?? "-", floor: loc.floor ?? "-" }),
    }),
  health: () => api<{ status: string; api: string; db: string }>("/api/health"),
  systemStatus: () =>
    api<{ overall: string; components: Record<string, { status: string; detail: string }> }>(
      "/api/system/status",
    ),
};
