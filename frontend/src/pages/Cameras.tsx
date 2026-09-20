import { Card, CardTitle } from "../components/ui";
import { MOCK_CAMERAS } from "../lib/api";

export default function Cameras() {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {MOCK_CAMERAS.map((c) => (
          <Card key={c.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-extrabold">{c.name}</h3>
                <p className="mt-0.5 text-sm text-slate-500">{c.location}</p>
              </div>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${
                  c.status === "online" ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500"
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${c.status === "online" ? "bg-emerald-500" : "bg-slate-400"}`} />
                {c.status.toUpperCase()}
              </span>
            </div>
            <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-2.5 text-sm">
              <span className="text-slate-500">AI pipeline</span>
              <span className="font-bold text-slate-700">
                {c.status === "online" ? "YOLO Pose · ByteTrack · Fall + Inactivity" : "—"}
              </span>
            </div>
          </Card>
        ))}
      </div>
      <Card>
        <CardTitle>How to connect a camera</CardTitle>
        <ol className="flex list-decimal flex-col gap-1.5 pl-5 text-sm text-slate-600">
          <li>Open the Dashboard and pick Laptop, Mobile, or Manual IP.</li>
          <li>For a phone: join the same Wi-Fi, start an IP-camera app, paste its URL.</li>
          <li>The backend runs detection and streams the annotated feed back here.</li>
        </ol>
      </Card>
    </div>
  );
}
