import { useState } from "react";
import CameraFeed from "../components/CameraFeed";
import { Card, CardTitle, ConfidenceBar, IconCamera, IconClock, IconSiren, StatCard, StatusBadge } from "../components/ui";
import { API_URL, DEFAULT_CAMERA_SOURCE, MOCK_CAMERAS, MOCK_INCIDENTS } from "../lib/api";

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

      {/* HERO camera panel — full width */}
      <Card>
        <CardTitle
          right={<span className="font-mono text-[11px] text-[#a8a08a]">{API_URL}</span>}
        >
          Live feed · Cam 01 · Main hallway
        </CardTitle>

        {/* Source rail */}
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
                  <span
                    className={`h-2 w-2 rounded-full ${active ? "rec-dot bg-emerald-400" : "bg-[#d8d2c2]"}`}
                  />
                </span>
                <span className={`mt-1 block text-xs ${active ? "text-[#a8a08a]" : "text-[#a8a08a]"}`}>
                  {m.hint}
                </span>
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

        {/* Legend + pipeline rail */}
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

      {/* Bottom row: night log + watch note */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
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

        <Card>
          <CardTitle>On watch</CardTitle>
          <p className="text-sm leading-relaxed text-[#57534a]">
            The desk watches <strong className="text-[#16130e]">fall → stillness → distress</strong> and
            only raises a hand when the evidence stacks up. Every red row still needs your eyes before it
            means anything.
          </p>
          <div className="mt-4 rounded-lg bg-[#16130e] p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">Score bands</p>
            <ul className="mt-2 flex flex-col gap-1.5 font-mono text-xs">
              <li className="flex justify-between"><span className="text-[#a8a08a]">0–39</span><span className="text-white">QUIET</span></li>
              <li className="flex justify-between"><span className="text-[#a8a08a]">40–69</span><span className="text-amber-400">WATCHING</span></li>
              <li className="flex justify-between"><span className="text-[#a8a08a]">70–100</span><span className="text-red-400">ALERT</span></li>
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
}
