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
      {/* Rail — narrow icon bar at every size */}
      <aside className="flex w-14 shrink-0 flex-col items-center bg-[#16130e] py-5 text-[#e8e4d8] xl:w-[72px]">
        <Link to="/" title="SilentSOS home" className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-[#c81e1e]">
          <span className="font-display text-lg font-bold text-white">S</span>
          <span className="rec-dot absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 border-[#16130e] bg-[#c81e1e]" />
        </Link>

        <nav className="mt-7 flex flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              title={item.label}
              aria-label={item.label}
              className={({ isActive }) =>
                `flex h-11 w-11 items-center justify-center rounded-lg transition-colors ${
                  isActive
                    ? "bg-[#26211a] text-white shadow-[inset_2px_0_0_#c81e1e]"
                    : "text-[#a8a08a] hover:bg-[#1e1a14] hover:text-white"
                }`
              }
            >
              {item.icon}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto flex flex-col items-center gap-3">
          <span title="System armed — local monitoring" className="rec-dot h-2 w-2 rounded-full bg-emerald-400" />
          <Link
            to="/login"
            title="Operator sign in"
            aria-label="Operator sign in"
            className="flex h-11 w-11 items-center justify-center rounded-lg border border-[#353022] text-[#e8e4d8] transition-colors hover:border-[#6b6558] hover:bg-[#1e1a14]"
          >
            <IconShield />
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
