import { useCallback, useEffect, useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident } from "../lib/api";
import { API_URL, DEFAULT_CAMERA_SOURCE, DataAPI, MOCK_INCIDENTS } from "../lib/api";
import { useLiveAlerts } from "../lib/useLiveAlerts";
import type { LiveIncident } from "../lib/useLiveAlerts";

type CamMode = "laptop" | "mobile" | "manual";

function load(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function save(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode — ignore */
  }
}

const PILL = (active: boolean): string =>
  `rounded-md px-3 py-1.5 font-mono text-[11px] font-bold tracking-widest transition-colors ${
    active ? "bg-[#16130e] text-white" : "bg-[#e9e5d8] text-[#57534a] hover:bg-[#dcd6c4]"
  }`;

const INPUT =
  "w-full rounded-md border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 font-mono text-xs focus:border-[#16130e] focus:outline-none";

/**
 * Sketch geometry: center column dominates (video fills, logs beneath),
 * alerts pinned to a fixed 300px right rail. Page is viewport-locked on xl.
 */
export default function Dashboard() {
  const [mode, setMode] = useState<CamMode>(() =>
    DEFAULT_CAMERA_SOURCE === "0" ? "laptop" : "mobile",
  );
  const [mobileUrl, setMobileUrl] = useState<string>(() =>
    load(
      "sos.cam.mobile",
      DEFAULT_CAMERA_SOURCE && DEFAULT_CAMERA_SOURCE !== "0"
        ? DEFAULT_CAMERA_SOURCE
        : "http://192.168.1.33:8080/video",
    ),
  );
  const [manualUrl, setManualUrl] = useState<string>(() => load("sos.cam.manual", ""));
  const [items, setItems] = useState<Incident[]>(MOCK_INCIDENTS);
  const [live, setLive] = useState(false);

  useEffect(() => {
    let dead = false;
    DataAPI.incidents()
      .then(
        (rows) =>
          !dead &&
          setItems(
            rows.map((a) => ({
              id: a.id,
              camera: `Cam #${a.camera_id}`,
              location: "—",
              eventType: a.event_type,
              confidence: Math.round(a.confidence * 100),
              time: new Date(a.timestamp).toLocaleString(),
              status: a.status,
            })),
          ),
      )
      .catch(() => {
        if (!dead) setItems(MOCK_INCIDENTS);
      });
    return () => {
      dead = true;
    };
  }, []);

  const onIncident = useCallback((inc: LiveIncident) => {
    setLive(true);
    setItems((prev) => [
      {
        id: inc.id,
        camera: inc.camera,
        location: "Live feed",
        eventType: inc.event_type,
        confidence: Math.round(inc.confidence * 100),
        time: new Date().toLocaleTimeString(),
        status: "OPEN",
      },
      ...prev,
    ]);
  }, []);
  useLiveAlerts(onIncident);

  const activeSource = mode === "laptop" ? "0" : mode === "mobile" ? mobileUrl : manualUrl;
  const openItems = items.filter((i) => i.status === "OPEN");

  return (
    <div className="flex flex-col gap-4 xl:h-full xl:min-h-0">
      {/* Slim status line */}
      <div className="flex shrink-0 flex-wrap items-center gap-x-5 gap-y-1 font-mono text-[11px] tracking-wider text-[#57534a]">
        <span>
          OPEN <strong className="text-[#c81e1e]">{openItems.length}</strong>
        </span>
        <span>
          ENGINE <strong className="text-[#3f6212]">ARMED</strong>
        </span>
        <span>
          FEED <strong className={live ? "text-[#3f6212]" : "text-[#a8a08a]"}>{live ? "● LIVE" : "○ LOCAL"}</strong>
        </span>
        <span className="ml-auto hidden sm:inline">{API_URL}</span>
      </div>

      {/* Center (video + logs) | right alerts rail */}
      <div className="grid grid-cols-1 gap-4 xl:min-h-0 xl:flex-1 xl:grid-cols-[minmax(0,1fr)_300px]">
        {/* CENTER — video fills, logs immediately beneath */}
        <div className="flex min-h-0 flex-col gap-4">
          <Card className="flex min-h-0 flex-1 flex-col">
            <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">CAM 01 · MAIN HALLWAY</span>}>
              Live feed
            </CardTitle>
            <div className="mb-3 flex shrink-0 flex-wrap items-center gap-2">
              <button className={PILL(mode === "laptop")} onClick={() => setMode("laptop")}>LAPTOP</button>
              <button className={PILL(mode === "mobile")} onClick={() => setMode("mobile")}>MOBILE</button>
              <button className={PILL(mode === "manual")} onClick={() => setMode("manual")}>MANUAL IP</button>
              {mode === "mobile" && (
                <input
                  value={mobileUrl}
                  onChange={(e) => {
                    setMobileUrl(e.target.value);
                    save("sos.cam.mobile", e.target.value);
                  }}
                  placeholder="http://192.168.1.33:8080/video"
                  spellCheck={false}
                  className={`${INPUT} min-w-52 flex-1`}
                />
              )}
              {mode === "manual" && (
                <input
                  value={manualUrl}
                  onChange={(e) => {
                    setManualUrl(e.target.value);
                    save("sos.cam.manual", e.target.value);
                  }}
                  placeholder="http://192.168.1.50:8080/video  ·  rtsp://user:pass@host/…"
                  spellCheck={false}
                  className={`${INPUT} min-w-52 flex-1`}
                />
              )}
            </div>
            <div className="min-h-0 flex-1">
              <CameraFeed source={activeSource} apiNote={API_URL} />
            </div>
            <div className="mt-3 flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-[#57534a]">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm bg-[#16a34a]" /> TRACKING
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm bg-[#f59e0b]" /> POSSIBLE FALL
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm bg-[#c81e1e]" /> EMERGENCY
              </span>
            </div>
          </Card>

          {/* LOGS — directly under the camera, center column only */}
          <Card className="shrink-0">
            <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">TAIL · {live ? "LIVE" : "DEMO"}</span>}>
              Logs
            </CardTitle>
            <ol className="flex max-h-36 flex-col divide-y divide-[#efece2] overflow-y-auto font-mono text-xs">
              {items.slice(0, 6).map((i) => (
                <li key={i.id} className="flex items-baseline gap-3 py-1.5">
                  <span className="shrink-0 tabular-nums text-[#a8a08a]">{i.time}</span>
                  <span
                    className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold tracking-widest ${
                      i.status === "OPEN" ? "bg-[#c81e1e] text-white" : "bg-[#e9e5d8] text-[#57534a]"
                    }`}
                  >
                    {i.status === "OPEN" ? "ALERT" : i.status}
                  </span>
                  <span className="truncate text-[#33302a]">
                    {i.eventType} — {i.location} · score {i.confidence}
                  </span>
                </li>
              ))}
            </ol>
          </Card>
        </div>

        {/* RIGHT — fixed 300px alerts rail */}
        <Card className="flex min-h-0 flex-col xl:overflow-hidden">
          <CardTitle
            right={
              <a href="/alerts" className="font-mono text-[11px] font-semibold text-[#c81e1e] hover:underline">
                ALL →
              </a>
            }
          >
            Alerts
          </CardTitle>
          {openItems.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-1 py-10 text-center">
              <p className="font-display font-bold">Queue clear</p>
              <p className="max-w-[180px] text-xs text-[#57534a]">Firings from the engine land here live.</p>
            </div>
          ) : (
            <ul className="flex flex-1 flex-col gap-3 overflow-y-auto pr-0.5">
              {openItems.slice(0, 8).map((i) => (
                <li key={i.id} className="rounded-lg border border-[#e2ddd0] bg-[#faf9f5] p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[11px] font-bold text-[#c81e1e]">#{i.id}</span>
                    <StatusBadge status={i.status} />
                  </div>
                  <p className="mt-1 text-[13px] font-bold leading-snug">{i.eventType}</p>
                  <p className="mt-0.5 font-mono text-[11px] text-[#a8a08a]">
                    {i.time} · {i.location}
                  </p>
                  <div className="mt-2">
                    <ConfidenceBar value={i.confidence} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
