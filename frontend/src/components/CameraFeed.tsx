import { useEffect, useState } from "react";
import { streamUrl } from "../lib/api";

interface Props {
  source: string;
  apiNote: string;
}

/** Live MJPEG feed from the backend AI pipeline. */
export default function CameraFeed({ source, apiNote }: Props) {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    setOffline(false);
  }, [source]);

  if (!source) {
    return (
      <div className="flex aspect-video flex-col items-center justify-center gap-1 rounded-xl bg-slate-950 px-6 text-center">
        <p className="font-semibold text-slate-200">No camera selected</p>
        <p className="max-w-sm text-sm text-slate-500">
          Pick a source above — laptop webcam, mobile IP, or a manual URL.
        </p>
      </div>
    );
  }

  if (offline) {
    return (
      <div className="flex aspect-video flex-col items-center justify-center gap-1 rounded-xl bg-slate-950 px-6 text-center">
        <p className="font-semibold text-slate-200">Camera offline</p>
        <p className="max-w-sm text-sm text-slate-500">
          Could not reach the stream. Verify the backend is running at {apiNote} and the camera URL is correct.
        </p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl bg-slate-950">
      <img
        key={source}
        src={streamUrl(source)}
        alt="Live AI camera feed"
        className="aspect-video w-full object-cover"
        onError={() => setOffline(true)}
      />
      <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-bold text-white">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />
        LIVE · AI TRACKING
      </span>
    </div>
  );
}
