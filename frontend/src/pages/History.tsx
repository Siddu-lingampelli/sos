import { useCallback, useEffect, useRef, useState } from "react";
import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident, IncidentStatus } from "../lib/api";
import { DataAPI, toIncident } from "../lib/api";

type Filter = "ALL" | IncidentStatus;

const FILTERS: Filter[] = ["ALL", "OPEN", "UNDER_REVIEW", "VERIFIED", "DISMISSED"];

export default function History() {
  // Backend rows only — empty means no history, never demo rows.
  const [items, setItems] = useState<Incident[]>([]);
  const [live, setLive] = useState(false);
  const [total, setTotal] = useState<number | null>(null);
  const [filter, setFilter] = useState<Filter>("ALL");
  // Monotonic request id: rapid filter clicks fire overlapping fetches, and a
  // slow ALL response must never overwrite a fast VERIFIED one (or pair its
  // items with another filter's total).
  const reqId = useRef(0);

  const load = useCallback(
    async (status: Filter) => {
      const id = reqId.current + 1;
      reqId.current = id;
      try {
        const [cameras, locations] = await Promise.all([
          DataAPI.cameras(),
          DataAPI.locations()
        ]);
        if (reqId.current !== id) return;
        const camMap = new Map(cameras.map(c => [c.id, c]));
        const locMap = new Map(locations.map(l => [l.id, l]));

        const rows = await DataAPI.history({ status: status === "ALL" ? undefined : status, limit: 100 });
        if (reqId.current !== id) return;
        const incidents = await Promise.all(rows.map(a => toIncident(a, camMap, locMap)));
        if (reqId.current !== id) return;
        setItems(incidents);
        setLive(true);
        const count = await DataAPI.historyCount({ status: status === "ALL" ? undefined : status });
        if (reqId.current !== id) return;
        setTotal(count.count);
      } catch {
        if (reqId.current !== id) return;
        setLive(false); // backend down — keep the empty table, say so
      }
    },
    [],
  );

  useEffect(() => {
    load(filter);
  }, [load, filter]);

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
          {total === null ? "…" : `${total} ${total === 1 ? "entry" : "entries"}`}
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          <span className="flex gap-1" role="tablist" aria-label="Status filter">
            {FILTERS.map((f) => (
              <button
                key={f}
                role="tab"
                aria-selected={filter === f}
                onClick={() => setFilter(f)}
                className={`rounded-md px-2 py-1 font-mono text-[10px] font-bold tracking-wide ${
                  filter === f ? "bg-[#16130e] text-white" : "bg-[#e9e5d8] text-[#57534a] hover:bg-[#dcd6c4]"
                }`}
              >
                {f === "ALL" ? "ALL" : f.replace("UNDER_REVIEW", "REVIEW")}
              </button>
            ))}
          </span>
          <span
            className={`rounded-md px-2.5 py-1 font-mono text-[11px] font-semibold ${
              live ? "bg-[#16130e] text-emerald-400" : "bg-[#c81e1e] text-white"
            }`}
          >
            {live ? "● LIVE FROM BACKEND" : "○ BACKEND DOWN"}
          </span>
        </div>
      </div>
      {items.length === 0 ? (
        <p className="py-6 text-center text-sm text-[#57534a]">
          {live ? "No incidents for this filter yet." : "Backend unreachable — start it to load history."}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-[#e2ddd0] font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">
                <th className="pb-3 pr-4 font-semibold">Ref</th>
                <th className="pb-3 pr-4 font-semibold">Event</th>
                <th className="pb-3 pr-4 font-semibold">Post</th>
                <th className="pb-3 pr-4 font-semibold">Time</th>
                <th className="pb-3 pr-4 font-semibold">Score</th>
                <th className="pb-3 font-semibold">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id} className="border-b border-[#efece2] last:border-0 hover:bg-[#faf9f5]">
                  <td className="py-3 pr-4 font-mono font-semibold">#{i.id}</td>
                  <td className="py-3 pr-4">
                    <p className="font-semibold">{i.eventType}</p>
                    <p className="font-mono text-[11px] text-[#a8a08a]">{i.camera}</p>
                  </td>
                  <td className="py-3 pr-4 text-[#57534a]">{i.location}</td>
                  <td className="py-3 pr-4 font-mono text-xs">{i.time}</td>
                  <td className="py-3 pr-4">
                    <ConfidenceBar value={i.confidence} />
                  </td>
                  <td className="py-3">
                    <StatusBadge status={i.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
