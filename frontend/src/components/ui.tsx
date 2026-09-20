import type { ReactNode } from "react";
import type { IncidentStatus } from "../lib/api";

const STATUS_STYLE: Record<IncidentStatus, string> = {
  OPEN: "bg-red-100 text-red-700 ring-red-200",
  UNDER_REVIEW: "bg-amber-100 text-amber-700 ring-amber-200",
  VERIFIED: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  DISMISSED: "bg-slate-200 text-slate-600 ring-slate-300",
};

export function StatusBadge({ status }: { status: IncidentStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${STATUS_STYLE[status]}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 70 ? "bg-red-500" : value >= 40 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-700">{value}%</span>
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      {children}
    </section>
  );
}

export function CardTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <h2 className="text-sm font-bold uppercase tracking-wide text-slate-500">{children}</h2>
      {right}
    </div>
  );
}

export function StatCard({ label, value, sub, accent }: { label: string; value: string; sub: string; accent: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${accent}`} />
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      </div>
      <p className="mt-2 text-3xl font-extrabold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{sub}</p>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl bg-slate-950 px-6 py-14 text-center">
      <p className="font-semibold text-slate-200">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{hint}</p>
    </div>
  );
}
