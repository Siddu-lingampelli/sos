import { useEffect, useState } from "react";
import { streamUrl } from "../lib/api";

interface Props {
  source: string;
  apiNote: string;
}

/** Live MJPEG feed from the backend AI pipeline, framed like a viewfinder. */
export default function CameraFeed({ source, apiNote }: Props) {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    setOffline(false);
  }, [source]);

  if (!source) {
    return (
      <div className="ops-grid flex aspect-video flex-col items-center justify-center gap-1 rounded-lg bg-[#16130e] px-6 text-center">
        <p className="font-display font-semibold text-[#f4f2ec]">No feed selected</p>
        <p className="max-w-sm text-sm text-[#a8a08a]">
          Choose laptop, mobile, or a manual URL above to open a live feed.
        </p>
      </div>
    );
  }

  if (offline) {
    return (
      <div className="ops-grid flex aspect-video flex-col items-center justify-center gap-1 rounded-lg bg-[#16130e] px-6 text-center">
        <p className="font-display font-semibold text-[#f4f2ec]">Feed unreachable</p>
        <p className="max-w-sm text-sm text-[#a8a08a]">
          Backend at {apiNote} isn't answering, or the camera URL is wrong. Check both and retry.
        </p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-lg bg-[#16130e]">
      <img
        key={source}
        src={streamUrl(source)}
        alt="Live AI camera feed"
        className="aspect-video w-full object-cover"
        onError={() => setOffline(true)}
      />
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
