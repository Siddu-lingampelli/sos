import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident, IncidentStatus } from "../lib/api";
import { DataAPI, toIncident } from "../lib/api";

const STAGES = ["Fall transition", "Observation window", "Inactivity check", "Confidence score", "Human verdict"];

export default function IncidentDetail() {
  const { id } = useParams();
  // Start empty: backend rows only. `undefined` = loading, `null` = not found.
  const [incident, setIncident] = useState<Incident | null | undefined>(undefined);
  const [events, setEvents] = useState<{ event_type: string; value: string | null; time: string }[]>([]);
  const [decideError, setDecideError] = useState<string | null>(null);
  const [eventsError, setEventsError] = useState<string | null>(null);

  useEffect(() => {
    // Strict id: /alert/1.5 or /alert/-3 must not hit /api/incidents/1.5.
    const num = /^\d+$/.test(id ?? "") ? Number(id) : NaN;
    if (!Number.isFinite(num)) {
      setIncident(null);
      return;
    }
    let dead = false;
    const load = async () => {
      try {
        const [row, cams, locs] = await Promise.all([
          DataAPI.incident(num),
          DataAPI.cameras(),
          DataAPI.locations()
        ]);
        if (dead) return;
        const camMap = new Map(cams.map(c => [c.id, c]));
        const locMap = new Map(locs.map(l => [l.id, l]));
        setIncident(await toIncident(row, camMap, locMap));
        // The dossier survives an events-fetch failure: a 404 on the
        // timeline used to masquerade as "incident not found".
        try {
          const evs = await DataAPI.incidentEvents(num);
          if (dead) return;
          setEvents(
            evs.map((e) => ({
              event_type: e.event_type,
              value: e.value,
              time: new Date(e.timestamp).toLocaleString(),
            })),
          );
        } catch {
          if (!dead) setEventsError("Evidence timeline unavailable — the dossier above is still valid.");
        }
      } catch {
        if (!dead) setIncident(null); // backend down or row gone — say so
      }
    };
    load();
    return () => { dead = true; };
  }, [id]);

  // A decided incident is a closed record — re-deciding it would rewrite
  // history rather than record a new human action. incident is possibly
  // undefined (loading) or null (not found); only OPEN/UNDER_REVIEW decide.
  const decidable = incident?.status === "OPEN" || incident?.status === "UNDER_REVIEW";

  const decide = useCallback(
    (status: IncidentStatus) => {
      if (!incident) return;
      setDecideError(null);
      DataAPI.setStatus(incident.id, status)
        .then((updated) => {
          setIncident((prev) =>
            prev
              ? {
                  ...prev,
                  status: updated.status,
                  confidence: Math.round(updated.confidence * 100),
                  eventType: updated.event_type,
                  time: new Date(updated.timestamp).toLocaleString(),
                }
              : prev,
          );
        })
        .catch((err: Error) => setDecideError(err.message));
    },
    [incident],
  );

  if (incident === undefined) {
    return (
      <Card>
        <p className="font-display font-bold">Loading dossier…</p>
        <p className="mt-1 text-sm text-[#57534a]">Fetching the record from the backend.</p>
      </Card>
    );
  }

  if (incident === null) {
    return (
      <Card>
        <p className="font-display font-bold">Dossier #{id} not found</p>
        <p className="mt-1 text-sm text-[#57534a]">Archived, erased, or the backend is unreachable.</p>
        <Link to="/history" className="mt-4 inline-block font-mono text-xs font-semibold text-[#c81e1e] hover:underline">
          ← BACK TO LOG
        </Link>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card className="border-l-2 border-l-[#c81e1e]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#c81e1e]">
              Possible emergency · #{incident.id}
            </p>
            <h2 className="mt-1 font-display text-2xl font-bold tracking-tight">{incident.eventType}</h2>
            <dl className="mt-4 grid max-w-lg grid-cols-2 gap-x-8 gap-y-2.5 text-sm">
              <dt className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">Location</dt>
              <dd className="font-semibold">{incident.location}</dd>
              <dt className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">Camera</dt>
              <dd className="font-semibold">{incident.camera}</dd>
              <dt className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">Time</dt>
              <dd className="font-mono font-semibold">{incident.time}</dd>
              <dt className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">Status</dt>
              <dd>
                <StatusBadge status={incident.status} />
              </dd>
            </dl>
          </div>
        </div>
        <div className="mt-4 max-w-xs">
          <ConfidenceBar value={incident.confidence} />
        </div>
        <div className="mt-4 flex flex-wrap gap-2 border-t border-[#e2ddd0] pt-4">
          {decidable && (
            <>
              <button
                onClick={() => decide("VERIFIED")}
                className="rounded-md bg-[#c81e1e] px-4 py-2 text-sm font-bold text-white hover:bg-[#8f1414]"
              >
                Verify emergency
              </button>
              <button
                onClick={() => decide("UNDER_REVIEW")}
                className="rounded-md bg-[#b45309] px-4 py-2 text-sm font-bold text-white hover:bg-[#92400e]"
              >
                Under review
              </button>
              <button
                onClick={() => decide("DISMISSED")}
                className="rounded-md bg-[#e9e5d8] px-4 py-2 text-sm font-bold text-[#57534a] hover:bg-[#dcd6c4]"
              >
                Dismiss
              </button>
            </>
          )}
          <Link
            to="/alerts"
            className="rounded-md border border-[#d8d2c2] px-4 py-2 text-sm font-bold hover:bg-[#faf9f5]"
          >
            ← Queue
          </Link>
          {decideError && <p className="w-full text-sm text-[#c81e1e]">{decideError}</p>}
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
          Detection timeline
        </h3>
        {eventsError && <p className="mb-2 text-xs text-[#b45309]">{eventsError}</p>}
        {events.length === 0 ? (
          <p className="text-xs text-[#57534a]">
            No per-frame evidence stored for this incident — the engine filed it on the fused score alone.
          </p>
        ) : (
          <ol className="flex max-h-64 flex-col gap-0 overflow-y-auto">
            {events.map((e) => (
              <li key={`${e.time}-${e.event_type}-${e.value}`} className="relative flex gap-4 pb-4 last:pb-0">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#16130e] font-mono text-[11px] font-bold text-white">
                  E
                </span>
                <div className="pt-1">
                  <p className="font-mono text-xs font-bold">{e.event_type}</p>
                  <p className="font-mono text-[11px] text-[#57534a]">
                    {e.time} · {e.value}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </Card>

      <Card>
        <h3 className="mb-4 font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
          How this alert was built
        </h3>
        <ol className="flex flex-col gap-0">
          {STAGES.map((s, idx) => (
            <li key={s} className="relative flex gap-4 pb-5 last:pb-0">
              {idx < STAGES.length - 1 && <span className="absolute left-[13px] top-7 h-full w-px bg-[#e2ddd0]" />}
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-mono text-[11px] font-bold ${
                  idx < 4 ? "bg-[#16130e] text-white" : "border border-dashed border-[#a8a08a] text-[#a8a08a]"
                }`}
              >
                {idx + 1}
              </span>
              <div className="pt-1">
                <p className="text-sm font-bold">{s}</p>
                <p className="text-xs text-[#57534a]">
                  {idx < 4 ? "Captured by the local pipeline." : "Your verdict above — recorded on this incident."}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
