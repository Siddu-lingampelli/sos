import { useEffect, useState, useRef } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { useCamera } from "../lib/camera";
import type { CamMode } from "../lib/camera";
import { AuthAPI, clearToken, isAuthed } from "../lib/api";
import { reconnectLiveSocket } from "../lib/liveSocket";
import { IconCamera, IconClock, IconGrid, IconPin, IconShield, IconSiren } from "./ui";
import SystemStatus from "./SystemStatus";
import AlertControls from "./AlertControls";
import { useLiveAlerts } from "../lib/useLiveAlerts";
import { requestNotificationPermission, notificationPermission } from "../lib/notifications";

const NAV = [
  { to: "/", label: "Overview", icon: <IconGrid /> },
  { to: "/alerts", label: "Live alerts", icon: <IconSiren /> },
  { to: "/history", label: "Incident log", icon: <IconClock /> },
  { to: "/cameras", label: "Cameras", icon: <IconCamera /> },
  { to: "/locations", label: "Locations", icon: <IconPin /> },
];

const TITLES: Record<string, { kicker: string; title: string }> = {
  "/": { kicker: "Operations", title: "Night desk overview" },
  "/alerts": { kicker: "Response queue", title: "Alerts awaiting a human" },
  "/history": { kicker: "Archive", title: "Incident log" },
  "/cameras": { kicker: "Coverage", title: "Cameras & posts" },
  "/locations": { kicker: "Coverage", title: "Locations" },
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

const VIEW_MODES: { id: CamMode; label: string }[] = [
  { id: "laptop", label: "Laptop" },
  { id: "mobile", label: "Mobile" },
  { id: "manual", label: "Manual" },
];

function ViewSwitch() {
  const { mode, setMode } = useCamera();
  return (
    <>
      <div
        role="tablist"
        aria-label="Camera view"
        className="hidden items-center gap-0.5 rounded-lg bg-[#e9e5d8] p-0.5 md:flex"
      >
        <span className="px-2 font-mono text-[10px] font-bold tracking-widest text-[#a8a08a]">VIEW</span>
        {VIEW_MODES.map((v) => (
          <button
            key={v.id}
            role="tab"
            aria-selected={mode === v.id}
            onClick={() => setMode(v.id)}
            className={`rounded-md px-2.5 py-1 font-mono text-[11px] font-bold tracking-wide transition-colors ${
              mode === v.id ? "bg-[#16130e] text-white" : "text-[#57534a] hover:bg-[#dcd6c4]"
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>
      <select
        aria-label="Camera view"
        value={mode}
        onChange={(e) => setMode(e.target.value as CamMode)}
        className="rounded-md border border-[#d8d2c2] bg-[#faf9f5] px-1.5 py-1 font-mono text-[11px] font-bold text-[#16130e] focus:outline-none md:hidden"
      >
        {VIEW_MODES.map((v) => (
          <option key={v.id} value={v.id}>
            {v.label}
          </option>
        ))}
      </select>
    </>
  );
}

export default function Layout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const base = "/" + (pathname.split("/")[1] ?? "");
  const head = TITLES[pathname] ?? TITLES[base] ?? { kicker: "SilentSOS", title: "Console" };
  const [signedIn, setSignedIn] = useState(isAuthed());

  // Layout never remounts across login/logout navigations, so re-read the
  // session flag whenever the route changes (login sets it before navigating).
  useEffect(() => {
    setSignedIn(isAuthed());
  }, [pathname]);

  // Level 9.1: Emergency overlay trigger via WebSocket
  const overlayTimerRef = useRef<number | null>(null);

  // Freed on unmount: a lingering timer would flash the overlay on a dead page.
  useEffect(() => {
    return () => {
      if (overlayTimerRef.current) window.clearTimeout(overlayTimerRef.current);
    };
  }, []);

  const triggerEmergencyOverlay = () => {
    const overlay = document.getElementById("sos-emergency-overlay");
    if (!overlay) return;
    overlay.classList.remove("hidden");
    const live = document.getElementById("sos-live-announcer");
    if (live) live.textContent = "Possible emergency detected. Human verification required.";
    if (overlayTimerRef.current) window.clearTimeout(overlayTimerRef.current);
    overlayTimerRef.current = window.setTimeout(() => {
      overlay.classList.add("hidden");
    }, 5000);
  };

  const signOut = (): void => {
    AuthAPI.logout()
      .catch(() => {
        /* offline logout still clears the local session */
      })
      .finally(() => {
        clearToken();
        setSignedIn(false);
        reconnectLiveSocket();
        navigate("/login");
      });
  };

  // Level 9.1: Notification permission banner
  useEffect(() => {
    const banner = document.getElementById("sos-perm-banner");
    const allowBtn = document.getElementById("sos-perm-allow");
    const dismissBtn = document.getElementById("sos-perm-dismiss");
    
    if (!banner) return;
    
    const perm = notificationPermission();
    if (perm === "default") {
      banner.classList.remove("hidden");
    }
    
    const onAllow = async () => {
      await requestNotificationPermission();
      banner.classList.add("hidden");
    };
    const onDismiss = () => {
      banner.classList.add("hidden");
    };
    
    allowBtn?.addEventListener("click", onAllow);
    dismissBtn?.addEventListener("click", onDismiss);
    
    return () => {
      allowBtn?.removeEventListener("click", onAllow);
      dismissBtn?.removeEventListener("click", onDismiss);
    };
  }, []);

  // Global socket: the single owner of sound + browser notifications.
  // Dashboard/Alerts mount their own silent sockets for list updates only,
  // so exactly one tone + one Notification fires per incident.
  useLiveAlerts(
    () => {
      triggerEmergencyOverlay();
    },
    undefined,
    undefined,
    undefined,
    undefined,
    { notify: true },
  );

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar — compact rail on phones (~18% per sketch), labeled rail on md+ */}
      <aside className="flex w-16 shrink-0 flex-col items-center bg-[#16130e] py-4 text-[#e8e4d8] md:w-36 md:items-stretch xl:w-40">
        <Link to="/" title="SilentSOS home" className="flex items-center gap-2.5 md:px-3.5">
          <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#c81e1e]">
            <span className="font-display text-base font-bold text-white">S</span>
            <span className="rec-dot absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 border-[#16130e] bg-[#c81e1e]" />
          </span>
          <span className="hidden min-w-0 md:block">
            <span className="block truncate font-display text-[15px] font-bold leading-tight tracking-tight text-white">
              SilentSOS
            </span>
            <span className="block font-mono text-[9px] uppercase tracking-[0.18em] text-[#a8a08a]">
              hostel watch
            </span>
          </span>
        </Link>

        <nav className="mt-6 flex flex-col gap-0.5 md:mt-7 md:px-2.5">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              title={item.label}
              className={({ isActive }) =>
                `flex h-10 w-10 items-center justify-center rounded-lg transition-colors md:h-auto md:w-auto md:gap-2.5 md:px-2.5 md:py-2 md:text-[12.5px] md:font-medium ${
                  isActive
                    ? "bg-[#26211a] text-white shadow-[inset_2px_0_0_#c81e1e]"
                    : "text-[#a8a08a] hover:bg-[#1e1a14] hover:text-white"
                }`
              }
            >
              <span className="shrink-0 opacity-80">{item.icon}</span>
              <span className="hidden truncate md:inline">{item.label}</span>
            </NavLink>
          ))}
        </nav>

          <div className="mt-auto flex flex-col items-center gap-2.5 md:items-stretch md:p-3">
            <span
              title="Armed — local monitoring"
              className="rec-dot h-2 w-2 rounded-full bg-emerald-400 md:hidden"
            />
            <div className="hidden rounded-lg border border-[#353022] bg-[#1e1a14] p-3 md:block">
              <p className="flex items-center gap-1.5 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
                <span className="rec-dot h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Armed
              </p>
              <p className="mt-1 text-[11px] leading-snug text-[#a8a08a]">
                Local only. Human verifies.
              </p>
            </div>
            {signedIn && pathname !== "/login" ? (
              <button
                onClick={signOut}
                title="Sign out"
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#353022] text-[#e8e4d8] transition-colors hover:border-[#6b6558] hover:bg-[#1e1a14] md:h-auto md:w-auto md:gap-2 md:px-3 md:py-2 md:text-xs md:font-semibold"
              >
                <IconShield />
                <span className="hidden md:inline">Sign out</span>
              </button>
            ) : (
              <Link
                to="/login"
                title="Operator sign in"
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#353022] text-[#e8e4d8] transition-colors hover:border-[#6b6558] hover:bg-[#1e1a14] md:h-auto md:w-auto md:gap-2 md:px-3 md:py-2 md:text-xs md:font-semibold"
              >
                <IconShield />
                <span className="hidden md:inline">Sign in</span>
              </Link>
            )}
          </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Screen-reader announcement for emergency firings. */}
        <div id="sos-live-announcer" role="alert" aria-live="assertive" className="sr-only" />
        {/* Level 9.1: Emergency alert overlay flash */}
        <div id="sos-emergency-overlay" role="alert" className="pointer-events-none fixed inset-0 z-[100] hidden bg-[#c81e1e] mix-blend-screen">
          <div className="absolute inset-0 animate-[sos-flash_1.6s_ease-in-out_infinite] bg-[#c81e1e] opacity-60" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="font-display text-[56px] font-black tracking-tight text-white uppercase">EMERGENCY</div>
              <div className="font-mono text-[12px] tracking-[0.3em] text-white/90 mt-2">POSSIBLE INCIDENT DETECTED</div>
            </div>
          </div>
        </div>

        {/* Level 9.1: Notification permission banner */}
        <div id="sos-perm-banner" className="hidden fixed top-0 left-0 right-0 z-[90] bg-[#16130e] text-white px-4 py-2 font-mono text-[11px]">
          <div className="flex items-center justify-between max-w-[1200px] mx-auto">
            <span>Enable browser notifications to receive emergency alerts even when the dashboard is in the background.</span>
            <div className="flex gap-2">
              <button
                id="sos-perm-allow"
                className="bg-[#c81e1e] px-3 py-1 rounded font-bold"
              >Allow</button>
              <button
                id="sos-perm-dismiss"
                className="border border-[#353022] px-3 py-1 rounded"
              >Dismiss</button>
            </div>
          </div>
        </div>

        <header className="flex shrink-0 items-center justify-between border-b border-[#e2ddd0] bg-[#f4f2ec]/90 px-5 py-3 backdrop-blur">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#a8a08a]">{head.kicker}</p>
            <h1 className="font-display text-lg font-bold leading-tight tracking-tight">{head.title}</h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="hidden lg:block">
              <AlertControls />
            </span>
            <ViewSwitch />
            <span className="hidden sm:block">
              <Clock />
            </span>
            <span className="hidden h-4 w-px bg-[#e2ddd0] sm:block" />
            <SystemStatus />
          </div>
        </header>
        <main className="min-h-0 flex-1 overflow-y-auto p-3 xl:overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

