/** Shared API config + domain types. Level 8 will replace mock data with fetches. */

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

export interface Camera {
  id: number;
  name: string;
  location: string;
  status: "online" | "offline";
  source: string;
}

/** Demo rows so reviewers can see the layout before Level 8 wires the API. */
export const MOCK_INCIDENTS: Incident[] = [
  {
    id: 101,
    camera: "Main Hallway",
    location: "Hostel Block B · Floor 2",
    eventType: "Fall + Prolonged Inactivity",
    confidence: 87,
    time: "11:30 PM",
    status: "OPEN",
  },
  {
    id: 100,
    camera: "Corridor East",
    location: "Hostel Block B · Floor 1",
    eventType: "Possible Fall (recovered)",
    confidence: 42,
    time: "09:15 PM",
    status: "DISMISSED",
  },
];

export const MOCK_CAMERAS: Camera[] = [
  { id: 1, name: "Main Hallway", location: "Hostel Block B · Floor 2", status: "online", source: "" },
  { id: 2, name: "Corridor East", location: "Hostel Block B · Floor 1", status: "offline", source: "" },
];

export function streamUrl(source: string, rotate = 0): string {
  return `${API_URL}/api/stream/video?source=${encodeURIComponent(source)}&rotate=${rotate}`;
}

export function wsUrl(): string {
  return `${API_URL.replace(/^http/, "ws")}/api/ws/alerts`;
}

/* ---- auth token (localStorage; Level 8 minimal session) ---- */

const TOKEN_KEY = "sos.token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

/* ---- typed API client (throws on HTTP error) ---- */

// Removed JWT/401 bounce for Level 8 local-only prototype
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers: { ...headers, ...(init?.headers ?? {}) } });
  } catch (err) {
    throw new Error(`Fetch failed to reach ${API_URL}${path} (Backend offline?)`);
  }

  if (!res.ok) {
    throw new Error(`API error ${res.status} on ${path}`);
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
export function toIncident(a: ApiIncident, cameraName?: string, locationName?: string): Incident {
  let time = a.timestamp;
  try {
    time = new Date(a.timestamp).toLocaleString();
  } catch {
    /* keep raw */
  }
  return {
    id: a.id,
    camera: cameraName ?? `Cam #${a.camera_id}`,
    location: locationName ?? "—",
    eventType: a.event_type,
    confidence: Math.round(a.confidence * 100),
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
};

export const DataAPI = {
  incidents: () => api<ApiIncident[]>("/api/incidents/"),
  active: () => api<ApiIncident[]>("/api/incidents/active"),
  setStatus: (id: number, status: IncidentStatus) =>
    api<ApiIncident>(`/api/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  cameras: () => api<ApiCamera[]>("/api/cameras/"),
  locations: () => api<ApiLocation[]>("/api/locations/"),
  health: () => api<{ status: string; api: string; db: string }>("/api/health"),
};
