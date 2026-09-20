import { useCallback, useEffect, useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, IconCamera, IconClock, IconSiren, StatCard, StatusBadge } from "../components/ui";
import type { Incident } from "../lib/api";
import { API_URL, DEFAULT_CAMERA_SOURCE, DataAPI, MOCK_CAMERAS, MOCK_INCIDENTS } from "../lib/api";
import { useLiveAlerts } from "../lib/useLiveAlerts";
import type { LiveIncident } from "../lib/useLiveAlerts";

type CamMode = "laptop" | "mobile" | "manual";

const MODES: { id: CamMode; label: string; hint: string }[] = [
  { id: "laptop", label: "Laptop", hint: "Built-in webcam · source 0" },
  { id: "mobile", label: "Mobile", hint: "Phone IP-camera app" },
  { id: "manual", label: "Manual IP", hint: "Any http / rtsp URL" },
];

const STAGES = ["Capture", "Pose", "Track", "Fall", "Still", "Score"];

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

const INPUT =
  "w-full rounded-md border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 font-mono text-xs focus:border-[#16130e] focus:outline-none";

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
  const openCount = items.filter((i) => i.status === "OPEN").length;
  const onlineCount = MOCK_CAMERAS.filter((c) => c.status === "online").length;

  return (
    <div className="flex flex-col gap-5">
      {/* Telemetry strip */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard label="Open alerts" value={String(openCount)} sub={live ? "live from engine" : "demo rows for now"} glyph={<IconSiren />} />
        <StatCard label="Cameras up" value={`${onlineCount}/${MOCK_CAMERAS.length}`} sub="posts reporting in" glyph={<IconCamera />} />
        <StatCard label="Logged" value={String(items.length)} sub={live ? "live from backend" : "demo rows for now"} glyph={<IconClock />} />
        <StatCard label="Pipeline" value="Armed" sub="local · no cloud calls" glyph={<IconSiren />} />
      </div>

      {/* Video + alerts side by side (per sketch) */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
        {/* VIDEO — the big box */}
        <Card className="xl:col-span-3">
          <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">CAM 01 · MAIN HALLWAY</span>}>
            Live feed
          </CardTitle>
          <div className="mb-4 grid grid-cols-1 gap-2 md:grid-cols-3">
            {MODES.map((m) => {
              const active = mode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`rounded-lg border px-4 py-3 text-left transition-colors ${
                    active
                      ? "border-[#16130e] bg-[#16130e] text-white"
                      : "border-[#e2ddd0] bg-[#faf9f5] hover:border-[#a8a08a]"
                  }`}
                >
                  <span className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold tracking-widest">{m.label.toUpperCase()}</span>
                    <span className={`h-2 w-2 rounded-full ${active ? "rec-dot bg-emerald-400" : "bg-[#d8d2c2]"}`} />
                  </span>
                  <span className="mt-1 block text-xs text-[#a8a08a]">{m.hint}</span>
                </button>
              );
            })}
          </div>
          {mode === "mobile" && (
            <input
              value={mobileUrl}
              onChange={(e) => {
                setMobileUrl(e.target.value);
                save("sos.cam.mobile", e.target.value);
              }}
              placeholder="http://192.168.1.33:8080/video"
              spellCheck={false}
              className={`${INPUT} mb-4`}
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
              className={`${INPUT} mb-4`}
            />
          )}
          <CameraFeed source={activeSource} apiNote={API_URL} />
          <div className="mt-4 flex flex-col gap-3 border-t border-[#e2ddd0] pt-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-[#57534a]">
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
            <ol className="flex flex-wrap items-center gap-1 font-mono text-[11px]">
              {STAGES.map((s, idx) => (
                <li key={s} className="flex items-center gap-1">
                  <span className="rounded bg-[#16130e] px-2 py-0.5 font-semibold text-emerald-400">
                    {s.toUpperCase()}
                  </span>
                  {idx < STAGES.length - 1 && <span className="text-[#d8d2c2]">→</span>}
                </li>
              ))}
            </ol>
          </div>
        </Card>

        {/* ALERTS — tall right rail */}
        <Card className="flex flex-col">
          <CardTitle
            right={
              <span className="flex items-center gap-2">
                {live && (
                  <span className="rounded bg-emerald-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-emerald-700">
                    LIVE
                  </span>
                )}
                <a href="/alerts" className="font-mono text-[11px] font-semibold text-[#c81e1e] hover:underline">
                  ALL →
                </a>
              </span>
            }
          >
            Alerts
          </CardTitle>
          {openCount === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-1 py-10 text-center">
              <p className="font-display font-bold">Queue clear</p>
              <p className="max-w-[180px] text-xs text-[#57534a]">Firings from the engine land here live.</p>
            </div>
          ) : (
            <ul className="flex flex-1 flex-col gap-3 overflow-y-auto">
              {items
                .filter((i) => i.status === "OPEN")
                .slice(0, 6)
                .map((i) => (
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

      {/* LOGS — full-width strip under the video */}
      <Card>
        <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">TAIL · {live ? "LIVE" : "DEMO"}</span>}>
          Logs
        </CardTitle>
        <ol className="flex flex-col divide-y divide-[#efece2] font-mono text-xs">
          {items.slice(0, 5).map((i) => (
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
  );
}
