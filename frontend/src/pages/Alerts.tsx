import { useState } from "react";
import { Link } from "react-router";
import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
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
    <div className="flex flex-col gap-6">
      {items.length === 0 && (
        <Card>
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-xl">✓</span>
            <div>
              <p className="font-bold">All clear — no open alerts</p>
              <p className="text-sm text-slate-500">New possible emergencies will appear here instantly.</p>
            </div>
          </div>
        </Card>
      )}

      {items.map((i) => (
        <Card key={i.id} className="border-l-4 border-l-red-500">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-red-600">🚨 Possible emergency</p>
              <h2 className="mt-1 text-lg font-extrabold">{i.eventType}</h2>
              <p className="mt-1 text-sm text-slate-500">
                {i.location} · Camera: {i.camera} · {i.time}
              </p>
            </div>
            <StatusBadge status={i.status} />
          </div>
          <div className="mt-4">
            <ConfidenceBar value={i.confidence} />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              onClick={() => decide(i.id, "VERIFIED")}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700"
            >
              Verify Emergency
            </button>
            <button
              onClick={() => decide(i.id, "DISMISSED")}
              className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-300"
            >
              Dismiss
            </button>
            <Link
              to={`/alert/${i.id}`}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-100"
            >
              Open Details
            </Link>
          </div>
        </Card>
      ))}

      {done.length > 0 && (
        <Card>
          <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Decided this session</h3>
          <ul className="flex flex-col gap-2">
            {done.map((i) => (
              <li key={i.id} className="flex items-center justify-between text-sm">
                <span>
                  <span className="font-bold">#{i.id}</span> {i.eventType}
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
