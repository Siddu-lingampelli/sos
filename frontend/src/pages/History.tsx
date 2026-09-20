import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import { MOCK_INCIDENTS } from "../lib/api";

export default function History() {
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wide text-slate-500">
          All incidents · {MOCK_INCIDENTS.length}
        </h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
          Demo rows — live API lands in Level 8
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <th className="pb-3 pr-4 font-bold">ID</th>
              <th className="pb-3 pr-4 font-bold">Event</th>
              <th className="pb-3 pr-4 font-bold">Location</th>
              <th className="pb-3 pr-4 font-bold">Time</th>
              <th className="pb-3 pr-4 font-bold">Confidence</th>
              <th className="pb-3 font-bold">Status</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_INCIDENTS.map((i) => (
              <tr key={i.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="py-3 pr-4 font-bold">#{i.id}</td>
                <td className="py-3 pr-4">
                  <p className="font-semibold">{i.eventType}</p>
                  <p className="text-xs text-slate-500">{i.camera}</p>
                </td>
                <td className="py-3 pr-4 text-slate-600">{i.location}</td>
                <td className="py-3 pr-4 text-slate-600">{i.time}</td>
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
