import { useCallback, useEffect, useState } from "react";
import { Card, CardTitle } from "../components/ui";
import { DataAPI, type ApiLocation } from "../lib/api";

/**
 * Location management (Level 8.7). Locations are the top of the
 * Location -> Camera -> status chain the plan requires the UI to expose.
 */
export default function Locations() {
  const [rows, setRows] = useState<ApiLocation[]>([]);
  const [live, setLive] = useState(false);
  const [name, setName] = useState("");
  const [building, setBuilding] = useState("");
  const [floor, setFloor] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    DataAPI.locations()
      .then((locs) => {
        setRows(locs);
        setLive(true);
      })
      .catch(() => setLive(false));
  }, []);

  useEffect(load, [load]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    DataAPI.createLocation({ name: name.trim(), building: building.trim(), floor: floor.trim() })
      .then(() => {
        setName("");
        setBuilding("");
        setFloor("");
        load();
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setBusy(false));
  };

  return (
    <div className="flex flex-col gap-5">
      <p className="font-mono text-[11px] tracking-wider text-[#57534a]">
        SOURCE <strong className={live ? "text-[#3f6212]" : "text-[#a8a08a]"}>{live ? "● BACKEND" : "○ BACKEND DOWN"}</strong>
      </p>

      <Card>
        <CardTitle>Add a location</CardTitle>
        <form onSubmit={submit} className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex flex-1 flex-col gap-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#a8a08a]">Name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Hostel Block B"
              className="rounded-lg border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#c81e1e]/30"
            />
          </label>
          <label className="flex flex-1 flex-col gap-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#a8a08a]">Building</span>
            <input
              value={building}
              onChange={(e) => setBuilding(e.target.value)}
              placeholder="Block B"
              className="rounded-lg border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#c81e1e]/30"
            />
          </label>
          <label className="flex flex-1 flex-col gap-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#a8a08a]">Floor</span>
            <input
              value={floor}
              onChange={(e) => setFloor(e.target.value)}
              placeholder="2"
              className="rounded-lg border border-[#d8d2c2] bg-[#faf9f5] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#c81e1e]/30"
            />
          </label>
          <button
            type="submit"
            disabled={busy || !name.trim()}
            className="h-[38px] rounded-lg bg-[#16130e] px-4 font-mono text-xs font-bold uppercase tracking-wider text-white transition-colors hover:bg-[#26211a] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Saving" : "Add"}
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-[#c81e1e]">{error}</p>}
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((l) => (
          <Card key={l.id}>
            <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a8a08a]">
              Post {String(l.id).padStart(2, "0")}
            </p>
            <h3 className="mt-0.5 font-display text-lg font-bold tracking-tight">{l.name}</h3>
            <p className="mt-0.5 text-sm text-[#57534a]">
              {[l.building, l.floor].filter((s) => s && s !== "-").join(" · ") || "—"}
            </p>
          </Card>
        ))}
        {live && rows.length === 0 && (
          <p className="text-sm text-[#57534a]">No locations yet — add the first one above.</p>
        )}
      </div>
    </div>
  );
}
