import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import { MOCK_INCIDENTS } from "../lib/api";

export default function History() {
  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
          {MOCK_INCIDENTS.length} entries
        </h2>
        <span className="rounded-md bg-[#e9e5d8] px-2.5 py-1 font-mono text-[11px] text-[#57534a]">
          DEMO ROWS — LIVE API IN LEVEL 8
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
            {MOCK_INCIDENTS.map((i) => (
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
