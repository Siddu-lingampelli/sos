import { useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident, IncidentStatus } from "../lib/api";
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
  `rounded-md px-3 py-1.5 font-mono text-[11px] font-bold tracking-widest transition-colors ${
    active ? "bg-[#16130e] text-white" : "bg-[#e9e5d8] text-[#57534a] hover:bg-[#dcd6c4]"
  }`;

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
  const [queue, setQueue] = useState<Incident[]>(() => MOCK_INCIDENTS.filter((i) => i.status === "OPEN"));

  const activeSource = mode === "laptop" ? "0" : mode === "mobile" ? mobileUrl : manualUrl;
  const onlineCount = MOCK_CAMERAS.filter((c) => c.status === "online").length;

  const decide = (id: number, status: IncidentStatus): void => {
    setQueue((prev) => prev.filter((i) => i.id !== id));
    void status;
  };

  const logLines = [
    ...queue.map((i) => ({
      time: i.time,
      tag: "ALERT",
      hot: true,
      text: `${i.eventType} — ${i.location} · score ${i.confidence}`,
    })),
    { time: "23:41:07", tag: "TRACK", hot: false, text: "ByteTrack holding 1 identity · Cam 01" },
    { time: "23:40:52", tag: "POSE", hot: false, text: "17-point skeleton stable · 12 fps" },
    { time: "23:40:11", tag: "AUDIO", hot: false, text: "VAD idle · no keyword in window" },
    { time: "23:39:48", tag: "SYS", hot: false, text: "Observation windows nominal · engine armed" },
  ];

  return (
    <div className="flex flex-col gap-5">
      {/* Slim status line */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-[11px] tracking-wider text-[#57534a]">
        <span>
          OPEN <strong className="text-[#c81e1e]">{queue.length}</strong>
        </span>
        <span>
          CAMS <strong className="text-[#16130e]">{onlineCount}/{MOCK_CAMERAS.length}</strong>
        </span>
        <span>
          ENGINE <strong className="text-[#3f6212]">ARMED</strong>
        </span>
        <span className="ml-auto hidden sm:inline">{API_URL}</span>
      </div>

      {/* Video + alerts side by side (per sketch) */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
        {/* VIDEO — the big box */}
        <Card className="xl:col-span-3">
          <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">CAM 01 · MAIN HALLWAY</span>}>
            Live feed
          </CardTitle>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <button className={PILL(mode === "laptop")} onClick={() => setMode("laptop")}>LAPTOP</button>
            <button className={PILL(mode === "mobile")} onClick={() => setMode("mobile")}>MOBILE</button>
            <button className={PILL(mode === "manual")} onClick={() => setMode("manual")}>MANUAL IP</button>
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
              className={`${INPUT} mb-3`}
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
              className={`${INPUT} mb-3`}
            />
          )}
          <CameraFeed source={activeSource} apiNote={API_URL} />
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-[#57534a]">
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

        {/* ALERTS — tall right rail */}
        <Card className="flex flex-col">
          <CardTitle right={<a href="/alerts" className="font-mono text-[11px] font-semibold text-[#c81e1e] hover:underline">ALL →</a>}>
            Alerts
          </CardTitle>
          {queue.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-1 py-10 text-center">
              <p className="font-display font-bold">Queue clear</p>
              <p className="max-w-[180px] text-xs text-[#57534a]">Firings from the engine land here live.</p>
            </div>
          ) : (
            <ul className="flex flex-1 flex-col gap-3 overflow-y-auto">
              {queue.map((i) => (
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
                  <div className="mt-2.5 flex gap-2">
                    <button
                      onClick={() => decide(i.id, "VERIFIED")}
                      className="flex-1 rounded-md bg-[#c81e1e] px-2 py-1.5 text-xs font-bold text-white hover:bg-[#8f1414]"
                    >
                      Verify
                    </button>
                    <button
                      onClick={() => decide(i.id, "DISMISSED")}
                      className="flex-1 rounded-md bg-[#e9e5d8] px-2 py-1.5 text-xs font-bold text-[#57534a] hover:bg-[#dcd6c4]"
                    >
                      Dismiss
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {/* LOGS — full-width strip under the video */}
      <Card>
        <CardTitle right={<span className="font-mono text-[11px] text-[#a8a08a]">TAIL · LIVE</span>}>
          Logs
        </CardTitle>
        <ol className="flex flex-col divide-y divide-[#efece2] font-mono text-xs">
          {logLines.map((l, idx) => (
            <li key={idx} className="flex items-baseline gap-3 py-1.5">
              <span className="shrink-0 tabular-nums text-[#a8a08a]">{l.time}</span>
              <span
                className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold tracking-widest ${
                  l.hot ? "bg-[#c81e1e] text-white" : "bg-[#e9e5d8] text-[#57534a]"
                }`}
              >
                {l.tag}
              </span>
              <span className="truncate text-[#33302a]">{l.text}</span>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
