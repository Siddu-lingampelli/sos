import { Card, CardTitle } from "../components/ui";
import { MOCK_CAMERAS } from "../lib/api";

export default function Cameras() {
  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {MOCK_CAMERAS.map((c) => (
          <Card key={c.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">
                  Post {String(c.id).padStart(2, "0")}
                </p>
                <h3 className="mt-0.5 font-display text-lg font-bold tracking-tight">{c.name}</h3>
                <p className="mt-0.5 text-sm text-[#57534a]">{c.location}</p>
              </div>
              <span
                className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-mono text-[11px] font-semibold ${
                  c.status === "online" ? "bg-[#16130e] text-emerald-400" : "bg-[#e9e5d8] text-[#57534a]"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${c.status === "online" ? "rec-dot bg-emerald-400" : "bg-[#a8a08a]"}`}
                />
                {c.status.toUpperCase()}
              </span>
            </div>
            <div className="mt-4 flex items-center justify-between rounded-lg bg-[#faf9f5] px-3.5 py-2.5 text-sm ring-1 ring-[#e2ddd0]">
              <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">Stack</span>
              <span className="font-mono text-xs font-semibold">
                {c.status === "online" ? "YOLO · TRACK · FALL · STILL" : "—"}
              </span>
            </div>
          </Card>
        ))}
      </div>
      <Card>
        <CardTitle>Putting a camera on the desk</CardTitle>
        <ol className="flex list-decimal flex-col gap-1.5 pl-5 text-sm leading-relaxed text-[#57534a]">
          <li>Open Overview and choose Laptop, Mobile, or Manual IP.</li>
          <li>Phone route: same Wi-Fi, any IP-camera app, paste the URL it shows.</li>
          <li>The backend scores every frame and streams the annotated feed back here.</li>
        </ol>
      </Card>
    </div>
  );
}
