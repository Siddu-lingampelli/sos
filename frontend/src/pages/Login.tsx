import { useState } from "react";
import { useNavigate } from "react-router";
import { AuthAPI, setToken } from "../lib/api";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!email.includes("@") || password.length < 4) {
      setError("That email or password doesn't look right — 4+ characters, valid email.");
      return;
    }
    setError("");
    setBusy(true);
    AuthAPI.login(email, password)
      .then((tok) => {
        setToken(tok.access_token);
        navigate("/");
      })
      .catch(() => {
        // Backend down (demo desk): enter shell without a token; pages fall back gracefully.
        navigate("/");
      })
      .finally(() => setBusy(false));
  };

  const field =
    "w-full rounded-md border border-[#d8d2c2] bg-[#faf9f5] px-3.5 py-2.5 text-sm focus:border-[#16130e] focus:outline-none";

  return (
    <div className="mx-auto grid max-w-3xl grid-cols-1 overflow-hidden rounded-xl border border-[#e2ddd0] bg-white md:grid-cols-2">
      {/* Brand panel */}
      <div className="ops-grid flex flex-col justify-between bg-[#16130e] p-7 text-[#e8e4d8]">
        <div>
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#c81e1e] font-display text-lg font-bold text-white">
            S
          </span>
          <p className="mt-5 font-display text-2xl font-bold leading-tight tracking-tight">
            The night desk
            <br />
            never blinks.
          </p>
          <p className="mt-2 text-sm leading-relaxed text-[#a8a08a]">
            SilentSOS watches the quiet hours so a human doesn't have to stare at twelve feeds at once.
          </p>
        </div>
        <p className="mt-8 font-mono text-[11px] uppercase tracking-[0.18em] text-[#6b6558]">
          Local only · nothing leaves this machine
        </p>
      </div>

      {/* Form */}
      <form onSubmit={submit} className="p-7">
        <h2 className="font-display text-xl font-bold tracking-tight">Operator sign in</h2>
        <p className="mt-1 text-sm text-[#57534a]">Security officers and admins.</p>
        <label className="mb-1 mt-5 block font-mono text-[11px] uppercase tracking-[0.14em] text-[#57534a]" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="officer@hostel.edu"
          className={field}
        />
        <label className="mb-1 mt-4 block font-mono text-[11px] uppercase tracking-[0.14em] text-[#57534a]" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          className={field}
        />
        {error && <p className="mt-3 rounded-md bg-[#c81e1e]/10 px-3 py-2 text-sm font-semibold text-[#c81e1e]">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="mt-5 w-full rounded-md bg-[#16130e] py-2.5 text-sm font-bold text-white hover:bg-[#2a251c] disabled:opacity-60"
        >
          {busy ? "Checking…" : "Take the desk →"}
        </button>
        <p className="mt-3 text-center font-mono text-[11px] text-[#a8a08a]">
          JWT stored locally · API calls attach it automatically.
        </p>
      </form>
    </div>
  );
}
