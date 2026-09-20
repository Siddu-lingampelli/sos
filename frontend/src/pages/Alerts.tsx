import { useState } from "react";
import { Link } from "react-router";
import { Card, ConfidenceBar, IconCheck, StatusBadge } from "../components/ui";
import type { Incident, IncidentStatus } from "../lib/api";
import { MOCK_INCIDENTS } from "../lib/api";

export default function Alerts() {
  const [items, setItems] = useState<Incident[]>(() => MOCK_INCIDENTS.filter((i) => i.status === "OPEN"));
  const [done, setDone] = useState<Incident[]>([]);

  const decide = (id: number, status: IncidentStatus): void => {
    const found = items.find((i) => i.id === id);
    if (!found) return;
    setItems((prev) => prev.filter((i) => i.id !== id));
    setDone((prev) => [{ ...found, status }, ...prev]);
  };

  return (
    <div className="flex flex-col gap-5">
      {items.length === 0 && (
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
              className="rounded-md bg-[#c81e1e] px-4 py-2 text-sm font-bold text-white hover:bg-[#8f1414]"
            >
              Verify emergency
            </button>
            <button
              onClick={() => decide(i.id, "DISMISSED")}
              className="rounded-md bg-[#e9e5d8] px-4 py-2 text-sm font-bold text-[#57534a] hover:bg-[#dcd6c4]"
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
