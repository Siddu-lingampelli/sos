import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident } from "../lib/api";
import { DataAPI, MOCK_INCIDENTS } from "../lib/api";

const STAGES = ["Fall transition", "Observation window", "Inactivity check", "Confidence score", "Human verdict"];

export default function IncidentDetail() {
  const { id } = useParams();
  const [incident, setIncident] = useState<Incident | undefined>(() =>
    MOCK_INCIDENTS.find((i) => String(i.id) === id),
  );

  useEffect(() => {
    const num = Number(id);
    if (!Number.isFinite(num)) return;
    let dead = false;
    DataAPI.incidents()
      .then((rows) => {
        if (dead) return;
        const found = rows.find((a) => a.id === num);
        if (found) {
          setIncident({
            id: found.id,
            camera: `Cam #${found.camera_id}`,
            location: "—",
            eventType: found.event_type,
            confidence: Math.round(found.confidence * 100),
            time: new Date(found.timestamp).toLocaleString(),
            status: found.status,
          });
        }
      })
      .catch(() => {
        /* offline — mock row */
      });
    return () => {
      dead = true;
    };
  }, [id]);

  if (!incident) {
    return (
      <Card>
        <p className="font-display font-bold">Dossier #{id} not found</p>
        <p className="mt-1 text-sm text-[#57534a]">Archived, or the link is wrong.</p>
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
          <button className="rounded-md bg-[#c81e1e] px-4 py-2 text-sm font-bold text-white hover:bg-[#8f1414]">
            Verify emergency
          </button>
          <button className="rounded-md bg-[#e9e5d8] px-4 py-2 text-sm font-bold text-[#57534a] hover:bg-[#dcd6c4]">
            Dismiss
          </button>
          <Link
            to="/alerts"
            className="rounded-md border border-[#d8d2c2] px-4 py-2 text-sm font-bold hover:bg-[#faf9f5]"
          >
            ← Queue
          </Link>
        </div>
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
                  {idx < 4 ? "Captured by the local pipeline." : "Waiting on you — live timeline streams here in Level 8."}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
