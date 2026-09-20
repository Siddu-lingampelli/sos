import type { ReactNode } from "react";
import type { IncidentStatus } from "../lib/api";

/* ---- stroke icon set (no emoji) ---- */

function Base({ children }: { children: ReactNode }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export const IconGrid = () => (
  <Base>
    <rect x="3" y="3" width="7" height="7" rx="1.5" />
    <rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" />
    <rect x="14" y="14" width="7" height="7" rx="1.5" />
  </Base>
);

export const IconSiren = () => (
  <Base>
    <path d="M12 3a7 7 0 0 1 7 7H5a7 7 0 0 1 7-7Z" />
    <path d="M12 10v4" />
    <circle cx="12" cy="17.5" r="1.4" />
    <path d="M4 21h16" />
  </Base>
);

export const IconClock = () => (
  <Base>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5V12l3 2" />
  </Base>
);

export const IconCamera = () => (
  <Base>
    <rect x="2.5" y="7" width="13" height="11" rx="2" />
    <path d="m15.5 10.5 6-3.5v10l-6-3.5" />
  </Base>
);

export const IconShield = () => (
  <Base>
    <path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6l-7-3Z" />
    <path d="m9.5 12 2 2 3.5-4" />
  </Base>
);

export const IconCheck = () => (
  <Base>
    <circle cx="12" cy="12" r="8.5" />
    <path d="m8.5 12.5 2.5 2.5 4.5-5.5" />
  </Base>
);

/* ---- status + data display ---- */

const STATUS_STYLE: Record<IncidentStatus, string> = {
  OPEN: "bg-[#c81e1e] text-white",
  UNDER_REVIEW: "bg-[#b45309] text-white",
  VERIFIED: "bg-[#3f6212] text-white",
  DISMISSED: "bg-[#57534a] text-white",
};

export function StatusBadge({ status }: { status: IncidentStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 font-mono text-[11px] font-semibold tracking-wide ${STATUS_STYLE[status]}`}
    >
      {status.replace("_", " ")}
    </span>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 70 ? "bg-[#c81e1e]" : value >= 40 ? "bg-[#b45309]" : "bg-[#3f6212]";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1 w-20 overflow-hidden rounded-full bg-[#e2ddd0]">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="font-mono text-xs font-semibold">{value}%</span>
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-[#e2ddd0] bg-white p-5 shadow-[0_1px_2px_rgba(22,19,14,0.06)] ${className}`}>
      {children}
    </section>
  );
}

export function CardTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">
        {children}
      </h2>
      {right}
    </div>
  );
}

export function StatCard({ label, value, sub, glyph }: { label: string; value: string; sub: string; glyph: ReactNode }) {
  return (
    <div className="rounded-xl border border-[#e2ddd0] bg-white p-5 shadow-[0_1px_2px_rgba(22,19,14,0.06)]">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-[#57534a]">{label}</p>
        <span className="text-[#a8a08a]">{glyph}</span>
      </div>
      <p className="mt-2 font-display text-[34px] font-bold leading-none tracking-tight">{value}</p>
      <p className="mt-2 text-xs text-[#57534a]">{sub}</p>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="ops-grid flex flex-col items-center justify-center rounded-lg bg-[#16130e] px-6 py-14 text-center">
      <p className="font-display font-semibold text-[#f4f2ec]">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-[#a8a08a]">{hint}</p>
    </div>
  );
}
