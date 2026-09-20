import { useEffect, useState } from "react";
import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import type { Incident } from "../lib/api";
import { DataAPI, MOCK_INCIDENTS } from "../lib/api";

export default function History() {
  const [items, setItems] = useState<Incident[]>(MOCK_INCIDENTS);
  const [live, setLive] = useState(false);

  useEffect(() => {
    let dead = false;
    DataAPI.incidents()
      .then(
        (rows) =>
          !dead &&
          (setItems(
            rows.map((a) => ({
              id: a.id,
              camera: `Cam #${a.camera_id}`,
              location: "—",
              eventType: a.event_type,
              confidence: Math.round(a.confidence * 100),
              time: new Date(a.timestamp).toLocaleString(),
              status: a.status,
            })),
          ),
          setLive(true)),
      )
      .catch(() => {
        /* offline — demo rows */
      });
    return () => {
      dead = true;
    };
  }, []);

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
          {items.length} entries
        </h2>
        <span
          className={`rounded-md px-2.5 py-1 font-mono text-[11px] font-semibold ${
            live ? "bg-[#16130e] text-emerald-400" : "bg-[#e9e5d8] text-[#57534a]"
          }`}
        >
          {live ? "● LIVE FROM BACKEND" : "DEMO ROWS — START BACKEND FOR LIVE"}
        </span>
      </div>
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
    </Card>
  );
}
