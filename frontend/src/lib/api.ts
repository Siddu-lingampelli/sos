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

export function streamUrl(source: string): string {
  return `${API_URL}/api/stream/video?source=${encodeURIComponent(source)}`;
}
