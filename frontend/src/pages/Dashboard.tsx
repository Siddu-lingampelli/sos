import { useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, IconCamera, IconClock, IconSiren, StatCard, StatusBadge } from "../components/ui";
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
  `rounded-md px-3.5 py-1.5 font-mono text-xs font-semibold tracking-wide transition-colors ${
    active ? "bg-[#16130e] text-white" : "bg-[#e9e5d8] text-[#57534a] hover:bg-[#dcd6c4]"
  }`;

const INPUT =
  "min-w-60 flex-1 rounded-md border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 font-mono text-xs focus:border-[#16130e] focus:outline-none";

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

  const activeSource = mode === "laptop" ? "0" : mode === "mobile" ? mobileUrl : manualUrl;
  const openCount = MOCK_INCIDENTS.filter((i) => i.status === "OPEN").length;
  const onlineCount = MOCK_CAMERAS.filter((c) => c.status === "online").length;

  return (
    <div className="flex flex-col gap-5">
      {/* Telemetry strip */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard label="Open alerts" value={String(openCount)} sub="waiting on a human" glyph={<IconSiren />} />
        <StatCard label="Cameras up" value={`${onlineCount}/${MOCK_CAMERAS.length}`} sub="posts reporting in" glyph={<IconCamera />} />
        <StatCard label="Logged today" value={String(MOCK_INCIDENTS.length)} sub="demo rows for now" glyph={<IconClock />} />
        <StatCard label="Pipeline" value="Armed" sub="local · no cloud calls" glyph={<IconSiren />} />
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Camera panel */}
        <Card className="xl:col-span-2">
          <CardTitle
            right={<span className="font-mono text-[11px] text-[#a8a08a]">{API_URL}</span>}
          >
            Live feed · Cam 01
          </CardTitle>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <button className={PILL(mode === "laptop")} onClick={() => setMode("laptop")}>
              LAPTOP
            </button>
            <button className={PILL(mode === "mobile")} onClick={() => setMode("mobile")}>
              MOBILE
            </button>
            <button className={PILL(mode === "manual")} onClick={() => setMode("manual")}>
              MANUAL IP
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
              className={`${INPUT} mb-3 w-full`}
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
              className={`${INPUT} mb-3 w-full`}
            />
          )}
          <CameraFeed source={activeSource} apiNote={API_URL} />
          <p className="mt-3 font-mono text-[11px] leading-relaxed text-[#a8a08a]">
            YOLO pose → ByteTrack → fall + inactivity, drawn on the frame by the backend.
          </p>
        </Card>

        {/* Night log */}
        <Card>
          <CardTitle right={<a href="/alerts" className="font-mono text-[11px] font-semibold text-[#c81e1e] hover:underline">QUEUE →</a>}>
            Night log
          </CardTitle>
          <ol className="relative flex flex-col gap-4 border-l border-[#e2ddd0] pl-4">
            {MOCK_INCIDENTS.slice(0, 4).map((i) => (
              <li key={i.id} className="relative">
                <span
                  className={`absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-white ${
                    i.status === "OPEN" ? "bg-[#c81e1e]" : "bg-[#a8a08a]"
                  }`}
                />
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[13px] font-bold leading-snug">{i.eventType}</p>
                </div>
                <p className="mt-0.5 font-mono text-[11px] text-[#a8a08a]">
                  {i.time} · {i.location}
                </p>
                <div className="mt-1.5 flex items-center gap-2">
                  <ConfidenceBar value={i.confidence} />
                  <StatusBadge status={i.status} />
                </div>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </div>
  );
}
