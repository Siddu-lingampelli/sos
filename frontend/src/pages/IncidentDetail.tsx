import { Link, useParams } from "react-router";
import { Card, ConfidenceBar, StatusBadge } from "../components/ui";
import { MOCK_INCIDENTS } from "../lib/api";

export default function IncidentDetail() {
  const { id } = useParams();
  const incident = MOCK_INCIDENTS.find((i) => String(i.id) === id);

  if (!incident) {
    return (
      <Card>
        <p className="font-bold">Incident #{id} not found</p>
        <p className="mt-1 text-sm text-slate-500">It may have been archived or the link is incorrect.</p>
        <Link to="/history" className="mt-4 inline-block text-sm font-bold text-red-600 hover:underline">
          ← Back to incident history
        </Link>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Card className="border-l-4 border-l-red-500">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-red-600">
              🚨 Possible emergency · #{incident.id}
            </p>
            <h2 className="mt-1 text-2xl font-extrabold">{incident.eventType}</h2>
            <dl className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
              <dt className="text-slate-500">Location</dt>
              <dd className="font-semibold">{incident.location}</dd>
              <dt className="text-slate-500">Camera</dt>
              <dd className="font-semibold">{incident.camera}</dd>
              <dt className="text-slate-500">Time</dt>
              <dd className="font-semibold">{incident.time}</dd>
              <dt className="text-slate-500">Status</dt>
              <dd>
                <StatusBadge status={incident.status} />
              </dd>
            </dl>
          </div>
        </div>
        <div className="mt-4 max-w-xs">
          <ConfidenceBar value={incident.confidence} />
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700">
            Verify Emergency
          </button>
          <button className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-300">
            Dismiss
          </button>
          <Link
            to="/alerts"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-100"
          >
            ← All alerts
          </Link>
        </div>
      </Card>
      <Card>
        <p className="text-sm text-slate-500">
          Detection timeline (fall transition → observation → inactivity → score) will stream here in Level 8 via
          WebSocket. Human verification is required before any emergency is treated as confirmed.
        </p>
      </Card>
    </div>
  );
}
