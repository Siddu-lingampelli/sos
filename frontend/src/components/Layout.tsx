import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { IconCamera, IconClock, IconGrid, IconShield, IconSiren } from "./ui";

const NAV = [
  { to: "/", label: "Overview", icon: <IconGrid /> },
  { to: "/alerts", label: "Live alerts", icon: <IconSiren /> },
  { to: "/history", label: "Incident log", icon: <IconClock /> },
  { to: "/cameras", label: "Cameras", icon: <IconCamera /> },
];

const TITLES: Record<string, { kicker: string; title: string }> = {
  "/": { kicker: "Operations", title: "Night desk overview" },
  "/alerts": { kicker: "Response queue", title: "Alerts awaiting a human" },
  "/history": { kicker: "Archive", title: "Incident log" },
  "/cameras": { kicker: "Coverage", title: "Cameras & posts" },
  "/login": { kicker: "Access", title: "Operator sign in" },
};

function Clock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span className="font-mono text-[13px] tabular-nums text-[#57534a]">
      {now.toLocaleTimeString([], { hour12: false })}
    </span>
  );
}

export default function Layout() {
  const { pathname } = useLocation();
  const base = "/" + (pathname.split("/")[1] ?? "");
  const head = TITLES[pathname] ?? TITLES[base] ?? { kicker: "SilentSOS", title: "Console" };

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Rail */}
      <aside className="flex w-[208px] shrink-0 flex-col bg-[#16130e] text-[#e8e4d8]">
        <Link to="/" className="flex items-center gap-3 px-5 pb-7 pt-6">
          <span className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-[#c81e1e]">
            <span className="font-display text-lg font-bold text-white">S</span>
            <span className="rec-dot absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 border-[#16130e] bg-[#c81e1e]" />
          </span>
          <span>
            <span className="block font-display text-[17px] font-bold leading-tight tracking-tight text-white">
              SilentSOS
            </span>
            <span className="block font-mono text-[10px] uppercase tracking-[0.18em] text-[#a8a08a]">
              hostel watch
            </span>
          </span>
        </Link>

        <p className="px-5 pb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-[#6b6558]">
          Console
        </p>
        <nav className="flex flex-col gap-0.5 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] font-medium transition-colors ${
                  isActive
                    ? "bg-[#26211a] text-white shadow-[inset_2px_0_0_#c81e1e]"
                    : "text-[#a8a08a] hover:bg-[#1e1a14] hover:text-white"
                }`
              }
            >
              <span className="opacity-80">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto p-4">
          <div className="ops-grid rounded-lg border border-[#353022] bg-[#1e1a14] p-4">
            <p className="flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
              <span className="rec-dot h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Monitoring
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-[#a8a08a]">
              Local pipeline only. Nothing leaves this machine until a human verifies.
            </p>
          </div>
          <Link
            to="/login"
            className="mt-3 flex items-center justify-center gap-2 rounded-lg border border-[#353022] px-3.5 py-2.5 text-[13px] font-semibold text-[#e8e4d8] transition-colors hover:border-[#6b6558] hover:bg-[#1e1a14]"
          >
            <IconShield />
            Operator sign in
          </Link>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 items-center justify-between border-b border-[#e2ddd0] bg-[#f4f2ec]/90 px-5 py-3 backdrop-blur">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#a8a08a]">{head.kicker}</p>
            <h1 className="font-display text-lg font-bold leading-tight tracking-tight">{head.title}</h1>
          </div>
          <div className="flex items-center gap-3">
            <Clock />
            <span className="hidden h-4 w-px bg-[#e2ddd0] sm:block" />
            <span className="inline-flex items-center gap-1.5 rounded-md bg-[#16130e] px-2.5 py-1 font-mono text-[11px] font-semibold text-emerald-400">
              <span className="rec-dot h-1.5 w-1.5 rounded-full bg-emerald-400" />
              NOMINAL
            </span>
          </div>
        </header>
        <main className="min-h-0 flex-1 overflow-y-auto p-4 xl:overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
