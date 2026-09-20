import { useEffect, useRef, useState } from "react";
import { wsUrl } from "./api";

export interface LiveIncident {
  id: number;
  camera: string;
  event_type: string;
  confidence: number;
  status: string;
}

export type WsState = "live" | "retrying" | "demo";

/**
 * Live alert socket. Appends fresh POSSIBLE_EMERGENCY firings via onIncident,
 * surfaces status updates via onUpdate. Auto-reconnects; reports "demo" when
 * the backend is unreachable so pages can fall back to local data.
 */
export function useLiveAlerts(
  onIncident: (inc: LiveIncident) => void,
  onUpdate?: (id: number, status: string) => void,
): WsState {
  const [state, setState] = useState<WsState>("retrying");
  const cb = useRef({ onIncident, onUpdate });
  cb.current = { onIncident, onUpdate };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let dead = false;
    let timer: number | undefined;

    const connect = (): void => {
      if (dead) return;
      try {
        ws = new WebSocket(wsUrl());
      } catch {
        setState("demo");
        timer = window.setTimeout(connect, 5000);
        return;
      }
      ws.onopen = () => setState("live");
      ws.onmessage = (ev: MessageEvent) => {
        try {
          const msg = JSON.parse(String(ev.data)) as Record<string, unknown>;
          if (msg["type"] === "incident") {
            cb.current.onIncident({
              id: Number(msg["id"]),
              camera: String(msg["camera"] ?? "?"),
              event_type: String(msg["event_type"] ?? "Possible emergency"),
              confidence: Number(msg["confidence"] ?? 0),
              status: "OPEN",
            });
          } else if (msg["type"] === "incident_updated" && cb.current.onUpdate) {
            cb.current.onUpdate(Number(msg["id"]), String(msg["status"]));
          }
        } catch {
          /* malformed frame — ignore */
        }
      };
      ws.onerror = () => {
        try {
          ws?.close();
        } catch {
          /* ignore */
        }
      };
      ws.onclose = () => {
        if (dead) return;
        setState("retrying");
        timer = window.setTimeout(connect, 3000);
      };
    };

    connect();
    return () => {
      dead = true;
      window.clearTimeout(timer);
      try {
        ws?.close();
      } catch {
        /* ignore */
      }
    };
  }, []);

  return state;
}
