import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";

const NAV = [
  { to: "/", label: "Dashboard", icon: "▦" },
  { to: "/alerts", label: "Live Alerts", icon: "🚨" },
  { to: "/history", label: "Incidents", icon: "🕘" },
  { to: "/cameras", label: "Cameras", icon: "📷" },
];

const TITLES: Record<string, string> = {
  "/": "Security Dashboard",
  "/alerts": "Live Alerts",
  "/history": "Incident History",
  "/cameras": "Cameras & Locations",
  "/login": "Sign In",
};

function Clock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return <span className="tabular-nums text-sm text-slate-400">{now.toLocaleTimeString()}</span>;
}

export default function Layout() {
  const { pathname } = useLocation();
  const base = "/" + (pathname.split("/")[1] ?? "");
  const title = TITLES[pathname] ?? TITLES[base] ?? "SilentSOS";

  return (
    <div className="flex min-h-screen bg-slate-100 text-slate-900">
      {/* Sidebar */}
      <aside className="flex w-60 shrink-0 flex-col bg-slate-950 text-slate-300">
        <Link to="/" className="flex items-center gap-2.5 px-5 pb-6 pt-6">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-600 text-lg font-black text-white">
            S
          </span>
          <span>
            <span className="block text-[15px] font-extrabold leading-tight text-white">SilentSOS</span>
            <span className="block text-[11px] font-medium text-slate-500">Emergency Detection</span>
          </span>
        </Link>
        <nav className="flex flex-col gap-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition-colors ${
                  isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900 hover:text-white"
                }`
              }
            >
              <span className="w-5 text-center">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto p-4">
          <div className="rounded-xl bg-slate-900 p-3.5">
            <p className="flex items-center gap-2 text-xs font-bold text-emerald-400">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
              SYSTEM ARMED
            </p>
            <p className="mt-1 text-[11px] leading-snug text-slate-500">
              Local AI pipeline monitoring. Human verification required for all alerts.
            </p>
          </div>
          <Link
            to="/login"
            className="mt-3 block rounded-xl border border-slate-800 px-3.5 py-2.5 text-center text-sm font-semibold text-slate-300 transition-colors hover:border-slate-600 hover:text-white"
          >
            Operator Sign In
          </Link>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-4">
          <h1 className="text-xl font-extrabold tracking-tight">{title}</h1>
          <div className="flex items-center gap-4">
            <Clock />
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              ALL SYSTEMS NORMAL
            </span>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
