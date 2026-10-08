import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import { Card, ConfidenceBar, IconCheck, StatusBadge } from "../components/ui";
import type { Incident, IncidentStatus } from "../lib/api";
import { DataAPI, toIncident } from "../lib/api";
import { useLiveAlerts } from "../lib/useLiveAlerts";
import type { LiveIncident } from "../lib/useLiveAlerts";

export default function Alerts() {
  // Backend rows only — empty means a clear queue, never demo rows.
  const [items, setItems] = useState<Incident[]>([]);
  const [done, setDone] = useState<Incident[]>([]);
  const [backendUp, setBackendUp] = useState(false);
  const [decideError, setDecideError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [rows, cameras, locations] = await Promise.all([
        DataAPI.active(),
        DataAPI.cameras(),
        DataAPI.locations()
      ]);
      const camMap = new Map(cameras.map(c => [c.id, c]));
      const locMap = new Map(locations.map(l => [l.id, l]));
      const incidents = await Promise.all(rows.map(a => toIncident(a, camMap, locMap)));
      setItems(incidents);
      setBackendUp(true);
    } catch {
      setBackendUp(false); // backend down — keep the empty queue, say so
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onIncident = useCallback(
    (inc: LiveIncident) => {
      setBackendUp(true);
      const confidence = Number.isFinite(inc.confidence) ? Math.round(inc.confidence * 100) : 0;
      setItems((prev) =>
        prev.some((i) => i.id === inc.id)
          ? prev
          : [
              {
                id: inc.id,
                camera: inc.camera,
                location: "Live feed",
                eventType: inc.event_type,
                confidence,
                time: new Date().toLocaleTimeString(),
                status: "OPEN",
              },
              ...prev,
            ],
      );
    },
    [],
  );

  const onUpdate = useCallback((id: number, status: string) => {
    // Empty status = incident_deleted; any other status = decided elsewhere.
    // Either way the row no longer belongs in the OPEN queue.
    void status;
    setItems((prev) => prev.filter((i) => i.id !== id));
  }, []);

  // Fired while the socket was down: refetch so the queue is not stale.
  const onReconnect = useCallback(() => {
    load();
  }, [load]);

  // Silent socket: Layout's global socket owns sound + notifications.
  const wsState = useLiveAlerts(onIncident, onUpdate, undefined, undefined, onReconnect);
  const live = wsState === "live";

  const decide = (id: number, status: IncidentStatus): void => {
    const found = items.find((i) => i.id === id);
    if (!found) return;
    setDecideError(null);
    // Optimistic: move the row immediately so the queue feels instant, roll
    // back into the queue if the PATCH fails (backend down, stale token…).
    // The failure is surfaced — a silent rollback once made operators believe
    // an emergency was verified when it wasn't.
    setItems((prev) => prev.filter((i) => i.id !== id));
    setDone((prev) => [{ ...found, status }, ...prev]);
    DataAPI.setStatus(id, status).catch((err: unknown) => {
      setItems((prev) => [found, ...prev]);
      setDone((prev) => prev.filter((i) => i.id !== id));
      setDecideError(
        `Decision on #${id} did NOT reach the backend — still OPEN. ${err instanceof Error ? err.message : "Retry."}`,
      );
    });
  };

  return (
    <div className="flex flex-col gap-5">
      <p className="font-mono text-[11px] tracking-wider text-[#57534a]">
        FEED{" "}
        <strong className={live ? "text-[#3f6212]" : "text-[#a8a08a]"}>
          {live ? "● LIVE" : backendUp ? "○ CONNECTING" : "○ BACKEND DOWN"}
        </strong>
        {"  ·  "}NEW FIRINGS ARRIVE WITHOUT REFRESH
      </p>

      {!backendUp && (
        <Card>
          <p className="font-display font-bold">Backend unreachable</p>
          <p className="text-sm text-[#57534a]">
            The queue below may be stale — decisions are disabled until the API answers again.
          </p>
        </Card>
      )}

      {backendUp && items.length === 0 && (
        <Card>
          <div className="flex items-center gap-3">
            <span className="text-[#3f6212]">
              <IconCheck />
            </span>
            <div>
              <p className="font-display font-bold">Queue is clear</p>
              <p className="text-sm text-[#57534a]">New possible emergencies land here the moment they score.</p>
            </div>
          </div>
        </Card>
      )}

      {decideError && (
        <Card>
          <p className="text-sm font-bold text-[#c81e1e]" role="alert">{decideError}</p>
        </Card>
      )}

      {items.map((i) => (
        <Card key={i.id} className="border-l-2 border-l-[#c81e1e]">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#c81e1e]">
                Possible emergency · #{i.id}
              </p>
              <h2 className="mt-1 font-display text-xl font-bold tracking-tight">{i.eventType}</h2>
              <p className="mt-1 font-mono text-xs text-[#57534a]">
                {i.location} · {i.camera} · {i.time}
              </p>
            </div>
            <StatusBadge status={i.status} />
          </div>
          <div className="mt-4 max-w-xs">
            <ConfidenceBar value={i.confidence} />
          </div>
          <div className="mt-4 flex flex-wrap gap-2 border-t border-[#e2ddd0] pt-4">
            <button
              onClick={() => decide(i.id, "VERIFIED")}
              disabled={!backendUp}
              className="rounded-md bg-[#c81e1e] px-4 py-2 text-sm font-bold text-white hover:bg-[#8f1414] disabled:opacity-40"
            >
              Verify emergency
            </button>
            <button
              onClick={() => decide(i.id, "UNDER_REVIEW")}
              disabled={!backendUp}
              className="rounded-md bg-[#b45309] px-4 py-2 text-sm font-bold text-white hover:bg-[#92400e] disabled:opacity-40"
            >
              Under review
            </button>
            <button
              onClick={() => decide(i.id, "DISMISSED")}
              disabled={!backendUp}
              className="rounded-md bg-[#e9e5d8] px-4 py-2 text-sm font-bold text-[#57534a] hover:bg-[#dcd6c4] disabled:opacity-40"
            >
              Dismiss
            </button>
            <Link
              to={`/alert/${i.id}`}
              className="rounded-md border border-[#d8d2c2] px-4 py-2 text-sm font-bold hover:bg-[#faf9f5]"
            >
              Dossier →
            </Link>
          </div>
        </Card>
      ))}

      {done.length > 0 && (
        <Card>
          <h3 className="mb-3 font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
            Decided this shift
          </h3>
          <ul className="flex flex-col gap-2">
            {done.map((i) => (
              <li key={i.id} className="flex items-center justify-between gap-3 text-sm">
                <span>
                  <span className="font-mono font-semibold">#{i.id}</span> {i.eventType}
                </span>
                <StatusBadge status={i.status} />
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
