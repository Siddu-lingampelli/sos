import { useCallback, useEffect, useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident } from "../lib/api";
import { API_URL, DataAPI } from "../lib/api";
import { useCamera } from "../lib/camera";
import { useLiveAlerts } from "../lib/useLiveAlerts";
import type { LiveActivity, LiveIncident } from "../lib/useLiveAlerts";

const INPUT =
  "w-full rounded-md border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 font-mono text-xs focus:border-[#16130e] focus:outline-none";

/**
 * Responsive geometry (positions only — see .dash-grid in index.css):
 *  desktop xl : [ video+logs | alerts ]  (alerts spans both rows)
 *  mobile     : [ video     | alerts/logs stacked ] (video spans both rows)
 * Same three cards, repositioned by grid areas. No duplicates.
 */
export default function Dashboard() {
  const { mode, mobileUrl, setMobileUrl, manualUrl, setManualUrl, activeSource } = useCamera();
  // Real backend rows only — never demo data. Empty means empty.
  const [items, setItems] = useState<Incident[]>([]);
  const [live, setLive] = useState(false);
  const [dbState, setDbState] = useState("unknown");
  const [backendUp, setBackendUp] = useState(false);
  const [activity, setActivity] = useState<{ time: string; tag: string; text: string }[]>([]);
  const [rotate, setRotate] = useState<number>(() => {
    try {
      const v = Number(localStorage.getItem("sos.cam.rotate"));
      return [0, 90, 180, 270].includes(v) ? v : 0;
    } catch {
      return 0;
    }
  });

  const cycleRotate = (): void => {
    const next = rotate === 0 ? 90 : rotate === 90 ? 180 : rotate === 180 ? 270 : 0;
    setRotate(next);
    try {
      localStorage.setItem("sos.cam.rotate", String(next));
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    let dead = false;
    DataAPI.incidents()
      .then((rows) => {
        if (dead) return;
        setBackendUp(true);
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
        );
      })
      .catch(() => {
        // backend down: stay empty, say so honestly below
      });
    DataAPI.health()
      .then((h) => {
        if (!dead) {
          setBackendUp(true);
          setDbState(h.db);
        }
      })
      .catch(() => {
        if (!dead) setDbState("down");
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
  const onActivity = useCallback((act: LiveActivity) => {
    setActivity((prev) =>
      [{ time: new Date().toLocaleTimeString(), tag: act.tag, text: act.text }, ...prev].slice(0, 10),
    );
  }, []);
  useLiveAlerts(onIncident, undefined, onActivity);

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

      <div className={`dash-grid xl:min-h-0 xl:flex-1 ${mode === "laptop" ? "dash-desktop" : "dash-mobile"}`}>
        {/* VIDEO */}
        <Card className="dash-video flex min-h-[320px] flex-col xl:min-h-0">
          <CardTitle
            right={
              <span className="flex items-center gap-2">
                <span className="font-mono text-[11px] text-[#a8a08a]">CAM 01</span>
                {(mode === "mobile" || mode === "manual") && (
                  <button
                    onClick={cycleRotate}
                    title="Rotate camera view"
                    className="rounded-md bg-[#e9e5d8] px-2 py-1 font-mono text-[11px] font-bold text-[#57534a] hover:bg-[#dcd6c4]"
                  >
                    ⟳ {rotate}°
                  </button>
                )}
              </span>
            }
          >
            Live feed
          </CardTitle>
          {(mode === "mobile" || mode === "manual") && (
            <input
              value={mode === "mobile" ? mobileUrl : manualUrl}
              onChange={(e) => {
                if (mode === "mobile") setMobileUrl(e.target.value);
                else setManualUrl(e.target.value);
              }}
              placeholder={
                mode === "mobile"
                  ? "http://192.168.1.33:8080/video"
                  : "http://192.168.1.50:8080/video  ·  rtsp://user:pass@host/…"
              }
              spellCheck={false}
              className={`${INPUT} mb-3`}
            />
          )}
          <div className="min-h-0 flex-1">
            <CameraFeed source={activeSource} rotate={rotate} apiNote={API_URL} />
          </div>
          <div className="mt-3 hidden shrink-0 flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-[#57534a] sm:flex">
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

        {/* LOGS — bottom of the right column, scrolls */}
        <Card className="dash-logs flex min-h-[140px] flex-col xl:min-h-0 xl:overflow-hidden">
          <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">TAIL · {live ? "LIVE" : "DEMO"}</span>}>
            Logs
          </CardTitle>
          <ol className="dash-logs-list flex min-h-0 flex-1 flex-col divide-y divide-[#efece2] overflow-y-auto font-mono text-xs">
            {!backendUp && (
              <li className="flex items-baseline gap-3 py-1.5">
                <span className="shrink-0 tabular-nums text-[#a8a08a]">--:--:--</span>
                <span className="shrink-0 rounded bg-[#c81e1e] px-1.5 py-0.5 text-[10px] font-bold tracking-widest text-white">
                  SYS
                </span>
                <span className="truncate text-[#33302a]">
                  Backend unreachable at {API_URL} — start it to get live logs
                </span>
              </li>
            )}
            {activity.map((a, idx) => (
              <li key={`live-${idx}`} className="flex items-baseline gap-3 bg-emerald-50/50 py-1.5">
                <span className="shrink-0 tabular-nums text-[#a8a08a]">{a.time}</span>
                <span className="shrink-0 rounded bg-[#16130e] px-1.5 py-0.5 text-[10px] font-bold tracking-widest text-emerald-400">
                  {a.tag}
                </span>
                <span className="truncate text-[#33302a]">{a.text}</span>
              </li>
            ))}
            {items.slice(0, 6).map((i) => (
              <li key={i.id} className="flex items-baseline gap-3 py-1.5">
                <span className="hidden shrink-0 tabular-nums text-[#a8a08a] min-[400px]:inline">{i.time}</span>
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
            {backendUp && (
              <li className="flex items-baseline gap-3 py-1.5">
                <span className="shrink-0 tabular-nums text-[#a8a08a]">--:--:--</span>
                <span className="shrink-0 rounded bg-[#e9e5d8] px-1.5 py-0.5 text-[10px] font-bold tracking-widest text-[#57534a]">
                  SYS
                </span>
                <span className="truncate text-[#33302a]">
                  Engine armed · fall + stillness + distress · backend db: {dbState}
                </span>
              </li>
            )}
          </ol>
        </Card>

        {/* ALERTS */}
        <Card className="dash-alerts flex min-h-0 flex-col">
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
            <div className="flex flex-1 flex-col items-center justify-center gap-1 py-8 text-center">
              <p className="font-display text-sm font-bold">Queue clear</p>
              <p className="max-w-[160px] text-[11px] text-[#57534a]">Engine firings land here live.</p>
            </div>
          ) : (
            <ul className="flex flex-1 flex-col gap-2.5 overflow-y-auto pr-0.5">
              {openItems.slice(0, 8).map((i) => (
                <li key={i.id} className="rounded-lg border border-[#e2ddd0] bg-[#faf9f5] p-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[11px] font-bold text-[#c81e1e]">#{i.id}</span>
                    <StatusBadge status={i.status} />
                  </div>
                  <p className="mt-1 text-xs font-bold leading-snug">{i.eventType}</p>
                  <div className="mt-1.5">
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
