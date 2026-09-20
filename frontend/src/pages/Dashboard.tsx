import { useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, StatCard, StatusBadge } from "../components/ui";
import { API_URL, DEFAULT_CAMERA_SOURCE, MOCK_CAMERAS, MOCK_INCIDENTS } from "../lib/api";

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
  `rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
    active ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-600 hover:bg-slate-300"
  }`;

const INPUT =
  "min-w-60 flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900";

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

  const pick = (m: CamMode): void => setMode(m);
  const activeSource = mode === "laptop" ? "0" : mode === "mobile" ? mobileUrl : manualUrl;
  const openCount = MOCK_INCIDENTS.filter((i) => i.status === "OPEN").length;
  const onlineCount = MOCK_CAMERAS.filter((c) => c.status === "online").length;

  return (
    <div className="flex flex-col gap-6">
      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard label="Active Alerts" value={String(openCount)} sub="Needs human verification" accent="bg-red-500" />
        <StatCard label="Cameras Online" value={`${onlineCount}/${MOCK_CAMERAS.length}`} sub="Across monitored blocks" accent="bg-emerald-500" />
        <StatCard label="Incidents Today" value={String(MOCK_INCIDENTS.length)} sub="Including demo rows" accent="bg-sky-500" />
        <StatCard label="Pipeline" value="Armed" sub="Local AI · no cloud APIs" accent="bg-amber-500" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Camera panel */}
        <Card className="xl:col-span-2">
          <CardTitle
            right={<span className="text-xs font-medium normal-case text-slate-400">Backend: {API_URL}</span>}
          >
            Live Camera
          </CardTitle>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <button className={PILL(mode === "laptop")} onClick={() => pick("laptop")}>
              💻 Laptop
            </button>
            <button className={PILL(mode === "mobile")} onClick={() => pick("mobile")}>
              📱 Mobile
            </button>
            <button className={PILL(mode === "manual")} onClick={() => pick("manual")}>
              ⌨️ Manual IP
            </button>
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
              className={`${INPUT} mb-4 w-full`}
            />
          )}
          {mode === "manual" && (
            <input
              value={manualUrl}
              onChange={(e) => {
                setManualUrl(e.target.value);
                save("sos.cam.manual", e.target.value);
              }}
              placeholder="Any stream URL — http://…:8080/video or rtsp://user:pass@host/…"
              spellCheck={false}
              className={`${INPUT} mb-4 w-full`}
            />
          )}
          <CameraFeed source={activeSource} apiNote={API_URL} />
        </Card>

        {/* Recent alerts */}
        <Card>
          <CardTitle right={<a href="/alerts" className="text-xs font-bold text-red-600 hover:underline">View all</a>}>
            Recent Alerts
          </CardTitle>
          <ul className="flex flex-col gap-3">
            {MOCK_INCIDENTS.slice(0, 4).map((i) => (
              <li key={i.id} className="rounded-xl border border-slate-200 p-3.5">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-bold">{i.eventType}</p>
                  <StatusBadge status={i.status} />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {i.location} · {i.time}
                </p>
                <div className="mt-2">
                  <ConfidenceBar value={i.confidence} />
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
