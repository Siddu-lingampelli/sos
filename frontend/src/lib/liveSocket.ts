import { useEffect, useRef, useState } from "react";
import { wsUrl, getAuthVersion } from "./api";
import { notifyIncident, playAlertTone } from "./notifications";

export interface LiveIncident {
  id: number;
  camera: string;
  event_type: string;
  confidence: number;
  status: string;
}

/** "live" = socket connected, "retrying" = backend unreachable, auto-retrying. */
export type WsState = "live" | "retrying";

export interface LiveActivity {
  tag: string;
  text: string;
}

export interface LiveSystem {
  component: string;
  status: string;
  detail: string;
  source?: string;
}

/** Reconnect backoff bounds, in ms. A dead backend must not cause every open
 *  tab to hammer the server on a fixed 3 s timer. */
const RETRY_MIN_MS = 1000;
const RETRY_MAX_MS = 30000;

interface Bundle {
  onIncident: (inc: LiveIncident) => void;
  onUpdate?: (id: number, status: string) => void;
  onActivity?: (act: LiveActivity) => void;
  onSystem?: (sys: LiveSystem) => void;
  onReconnect?: () => void;
  notify: boolean;
}

/**
 * One WebSocket per tab, shared by every mounted page.
 *
 * Previously Layout + Dashboard/Alerts each opened their own socket (2× per
 * tab, 2N across N tabs) against /api/ws/alerts. Now the first subscriber
 * connects and the last unsubscribe closes; every subscriber gets every
 * message. Sound + browser notifications fire once per incident total:
 * only bundles created with notify:true trigger them.
 *
 * Auth: each (re)connect mints a fresh 90-second single-use ticket over the
 * authed API. The long-lived JWT never appears in the WS URL.
 */
const subs = new Set<Bundle>();
let ws: WebSocket | null = null;
let dead = false;
let timer: number | undefined;
let attempt = 0;
let everConnected = false;
let live = false;
/** Auth version the current (or last attempted) connection was made with. */
let connectedAuthVersion = -1;
const stateListeners = new Set<(s: WsState) => void>();

function setLive(v: boolean): void {
  live = v;
  const s: WsState = v ? "live" : "retrying";
  stateListeners.forEach((fn) => fn(s));
}

function validId(raw: unknown): number | null {
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function scheduleReconnect(): void {
  if (dead) return;
  setLive(false);
  const base = Math.min(RETRY_MAX_MS, RETRY_MIN_MS * 2 ** attempt);
  const delay = base / 2 + Math.random() * (base / 2);
  attempt += 1;
  timer = window.setTimeout(connect, delay);
}

function connect(): void {
  if (dead || subs.size === 0) return;
  connectedAuthVersion = getAuthVersion();
  // Ticket first: no ticket (logged out / expired session) means don't even
  // open the socket — the 401 surfaces as "retrying" until login.
  wsUrl().then(
    (url) => {
      if (dead || subs.size === 0) return;
      let socket: WebSocket;
      try {
        socket = new WebSocket(url);
      } catch {
        scheduleReconnect();
        return;
      }
      ws = socket;
      ws.onopen = () => {
        setLive(true);
        if (everConnected) {
          // Incidents that fired while disconnected were never delivered.
          subs.forEach((b) => b.onReconnect?.());
        }
        everConnected = true;
        attempt = 0;
      };
      ws.onmessage = (ev: MessageEvent) => {
        try {
          const msg = JSON.parse(String(ev.data)) as Record<string, unknown>;
          const type = String(msg["type"] ?? "");
          if (type === "notification" || type === "incident") {
            const id = validId(msg["id"] ?? msg["incident_id"] ?? 0);
            if (id === null) return; // never key rows on id 0
            const conf = Number(msg["confidence"] ?? 0);
            const inc: LiveIncident = {
              id,
              camera: String(msg["camera"] ?? "?"),
              event_type: String(msg["event_type"] ?? "Possible emergency"),
              confidence: Number.isFinite(conf) ? conf : 0,
              status: "OPEN",
            };
            subs.forEach((b) => b.onIncident(inc));
            if ([...subs].some((b) => b.notify)) {
              notifyIncident(inc.event_type, inc.confidence, inc.camera, inc.id);
              playAlertTone();
            }
          } else if (type === "incident_updated" || type === "incident_deleted") {
            const id = validId(msg["id"] ?? 0);
            if (id === null) return;
            // Deletion surfaces with an empty status so queues drop the row.
            const status = type === "incident_deleted" ? "" : String(msg["status"]);
            subs.forEach((b) => b.onUpdate?.(id, status));
          } else if (type === "ping") {
            try {
              ws?.send("pong");
            } catch {
              /* socket going away; onclose will reconnect */
            }
          } else if (type === "activity") {
            const act = { tag: String(msg["tag"] ?? "SYS"), text: String(msg["text"] ?? "") };
            subs.forEach((b) => b.onActivity?.(act));
          } else if (type === "system") {
            const sys = {
              component: String(msg["component"] ?? "system"),
              status: String(msg["status"] ?? "unknown"),
              detail: String(msg["detail"] ?? ""),
              source: msg["source"] ? String(msg["source"]) : undefined,
            };
            subs.forEach((b) => b.onSystem?.(sys));
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
        scheduleReconnect();
      };
    },
    () => {
      // Ticket mint failed (logged out or backend down) — back off, retry.
      scheduleReconnect();
    },
  );
}

/** Immediately drop the current socket and reconnect (post-login/logout). */
export function reconnectLiveSocket(): void {
  window.clearTimeout(timer);
  try {
    ws?.close();
  } catch {
    /* ignore */
  }
  ws = null;
  attempt = 0;
  if (subs.size > 0) connect();
  else setLive(false);
}

function subscribe(b: Bundle): () => void {
  subs.add(b);
  if (subs.size === 1) {
    dead = false;
    connect();
  } else if (!live || getAuthVersion() !== connectedAuthVersion) {
    // Dead socket, or the session changed (login/logout) while usable
    // sockets exist: reconnect so the new session's ticket is used at once.
    reconnectLiveSocket();
  } else {
    b.onReconnect?.();
  }
  return () => {
    subs.delete(b);
    if (subs.size === 0) {
      window.clearTimeout(timer);
      try {
        ws?.close();
      } catch {
        /* ignore */
      }
      ws = null;
      setLive(false);
    }
  };
}

/**
 * Live alert socket (shared singleton). Same callback contract as before;
 * pages that only need list updates pass no opts (silent).
 */
export function useLiveAlerts(
  onIncident: (inc: LiveIncident) => void,
  onUpdate?: (id: number, status: string) => void,
  onActivity?: (act: LiveActivity) => void,
  onSystem?: (sys: LiveSystem) => void,
  /** Called after every successful (re)connect. Pages use it to re-fetch
   *  state that fired while the socket was down and was therefore missed. */
  onReconnect?: () => void,
  /** Fire browser notification + tone here. Only Layout's global socket
   *  passes notify: true. */
  opts?: { notify?: boolean },
): WsState {
  const [state, setState] = useState<WsState>(live ? "live" : "retrying");
  const cb = useRef({ onIncident, onUpdate, onActivity, onSystem, onReconnect });
  cb.current = { onIncident, onUpdate, onActivity, onSystem, onReconnect };
  const notifyRef = useRef(opts?.notify ?? false);
  notifyRef.current = opts?.notify ?? false;
  // Reconnect when the auth session changes (login/logout) so the socket
  // never runs anonymous after a login or authed after a logout.
  const authVersion = getAuthVersion();

  useEffect(() => {
    const bundle: Bundle = {
      onIncident: (inc) => cb.current.onIncident(inc),
      onUpdate: (id, s) => cb.current.onUpdate?.(id, s),
      onActivity: (a) => cb.current.onActivity?.(a),
      onSystem: (s) => cb.current.onSystem?.(s),
      onReconnect: () => cb.current.onReconnect?.(),
      notify: notifyRef.current,
    };
    const unsub = subscribe(bundle);
    const listener = (s: WsState): void => setState(s);
    stateListeners.add(listener);
    setState(live ? "live" : "retrying");
    return () => {
      stateListeners.delete(listener);
      unsub();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authVersion]);

  return state;
}
