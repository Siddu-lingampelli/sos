import { useEffect, useState } from "react";
import { DataAPI, isAuthed } from "../lib/api";

interface ComponentState {
  status: string;
  detail: string;
}

/** Polls backend component health so a dead camera/AI/DB is visible here.
 *  Polls only while signed in (the endpoint requires auth) and only while
 *  the tab is visible — logged-out and hidden tabs stay silent. */
export default function SystemStatus() {
  const [overall, setOverall] = useState("unknown");
  const [components, setComponents] = useState<Record<string, ComponentState>>({});

  useEffect(() => {
    let dead = false;
    const poll = (): void => {
      if (!isAuthed()) return;
      if (typeof document !== "undefined" && document.hidden) return;
      DataAPI.systemStatus()
        .then((s) => {
          if (dead) return;
          setOverall(s.overall);
          setComponents(s.components ?? {});
        })
        .catch(() => {
          if (!dead) {
            setOverall("down");
            setComponents({ backend: { status: "down", detail: "unreachable" } });
          }
        });
    };
    poll();
    const t = setInterval(poll, 5000);
    const onVisible = (): void => {
      if (!document.hidden) poll();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      dead = true;
      clearInterval(t);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  const tone =
    overall === "ok"
      ? "bg-[#16130e] text-emerald-400"
      : overall === "degraded"
        ? "bg-[#f59e0b] text-[#16130e]"
        : "bg-[#c81e1e] text-white";

  const detail = Object.entries(components)
    .filter(([, c]) => c.status !== "ok")
    .map(([name, c]) => `${name}: ${c.status}`)
    .join(" · ");

  return (
    <span
      title={detail || "All components nominal"}
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-mono text-[11px] font-semibold ${tone}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {overall.toUpperCase()}
    </span>
  );
}