import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router";
import { AuthAPI, isAuthed, setAuthed } from "../lib/api";
import Login from "../pages/Login";

/** Blocks unauthenticated rendering of the console. On mount (and only when
 *  no in-memory session exists) it probes /users/me, which succeeds on the
 *  httpOnly cookie alone — so a reload restores the session with no token in
 *  JS-accessible storage. Failure bounces to /login. */
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [state, setState] = useState<"checking" | "ok" | "denied">(
    isAuthed() ? "ok" : "checking",
  );
  useEffect(() => {
    if (isAuthed()) {
      setState("ok");
      return;
    }
    let dead = false;
    AuthAPI.me()
      .then(() => {
        if (dead) return;
        setAuthed(true);
        setState("ok");
      })
      .catch(() => {
        if (!dead) setState("denied");
      });
    return () => {
      dead = true;
    };
  }, []);
  if (state === "checking") {
    return (
      <div className="flex h-screen items-center justify-center bg-[#f4f2ec]">
        <p className="font-mono text-xs tracking-widest text-[#57534a]">CHECKING SESSION…</p>
      </div>
    );
  }
  if (state === "denied") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}

/** Signed-in operators hitting /login go straight to the desk. */
export function LoginRoute() {
  const [state, setState] = useState<"checking" | "login" | "desk">(
    isAuthed() ? "desk" : "checking",
  );
  useEffect(() => {
    if (isAuthed()) {
      setState("desk");
      return;
    }
    let dead = false;
    AuthAPI.me()
      .then(() => {
        if (dead) return;
        setAuthed(true);
        setState("desk");
      })
      .catch(() => {
        if (!dead) setState("login");
      });
    return () => {
      dead = true;
    };
  }, []);
  if (state === "checking") {
    return (
      <div className="flex h-screen items-center justify-center bg-[#f4f2ec]">
        <p className="font-mono text-xs tracking-widest text-[#57534a]">CHECKING SESSION…</p>
      </div>
    );
  }
  if (state === "desk") return <Navigate to="/" replace />;
  return <Login />;
}
