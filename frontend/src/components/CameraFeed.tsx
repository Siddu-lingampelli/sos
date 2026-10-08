import { useEffect, useState } from "react";
import { streamUrl } from "../lib/api";

interface Props {
  source: string;
  rotate: number;
}

/** Live MJPEG feed — fills its parent (viewfinder chrome overlaid). */
export default function CameraFeed({ source, rotate }: Props) {
  const [offline, setOffline] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    setOffline(false);
    setAttempt(0);
    setSrc(null);
  }, [source, rotate]);

  // The feed URL carries a 90-second single-use ticket minted over the authed
  // API — fetched fresh per source/rotation/attempt so an expired ticket
  // retries with a new one instead of wedging the <img> on a 401.
  useEffect(() => {
    if (!source || offline) return;
    let dead = false;
    streamUrl(source, rotate)
      .then((url) => {
        if (!dead) setSrc(url);
      })
      .catch(() => {
        if (!dead) setOffline(true);
      });
    return () => {
      dead = true;
    };
  }, [source, rotate, attempt, offline]);

  if (!source) {
    return (
      <div className="ops-grid flex h-full min-h-[280px] w-full flex-col items-center justify-center gap-1 rounded-lg bg-[#16130e] px-6 text-center">
        <p className="font-display font-semibold text-[#f4f2ec]">No feed selected</p>
        <p className="max-w-sm text-sm text-[#a8a08a]">
          Choose laptop, mobile, or a manual URL above to open a live feed.
        </p>
      </div>
    );
  }

  if (offline) {
    return (
      <div className="ops-grid flex h-full min-h-[280px] w-full flex-col items-center justify-center gap-1 rounded-lg bg-[#16130e] px-6 text-center">
        <p className="font-display font-semibold text-[#f4f2ec]">Feed unreachable</p>
        <p className="max-w-sm text-sm text-[#a8a08a]">
          The backend isn't answering, or the camera URL is wrong. Check both and retry.
        </p>
        <button
          onClick={() => {
            setOffline(false);
            setAttempt((a) => a + 1); // bust the img cache so it re-requests
          }}
          className="mt-3 rounded-md bg-[#c81e1e] px-4 py-2 text-sm font-bold text-white hover:bg-[#8f1414]"
        >
          Retry feed
        </button>
      </div>
    );
  }

  return (
    <div className="relative h-full min-h-[280px] w-full overflow-hidden rounded-lg bg-[#16130e]">
      {src ? (
        <img
          key={`${source}|${rotate}|${attempt}`}
          src={src}
          alt="Live AI camera feed"
          className="absolute inset-0 h-full w-full object-cover"
          onError={() => setOffline(true)}
        />
      ) : (
        <div className="ops-grid absolute inset-0 flex flex-col items-center justify-center gap-1 px-6 text-center">
          <p className="font-display font-semibold text-[#f4f2ec]">Opening feed…</p>
          <p className="max-w-sm text-sm text-[#a8a08a]">Requesting a secure stream ticket.</p>
        </div>
      )}
      <span className="vf-corner vf-tl" />
      <span className="vf-corner vf-tr" />
      <span className="vf-corner vf-bl" />
      <span className="vf-corner vf-br" />
      <span className="absolute left-4 top-4 inline-flex items-center gap-1.5 rounded bg-black/65 px-2 py-1 font-mono text-[11px] font-semibold tracking-wider text-white">
        <span className="rec-dot h-1.5 w-1.5 rounded-full bg-[#ff3b30]" />
        REC · POSE TRACKING
      </span>
      <span className="absolute bottom-4 right-4 rounded bg-black/65 px-2 py-1 font-mono text-[11px] tabular-nums text-white/80">
        CAM 01
      </span>
    </div>
  );
}
