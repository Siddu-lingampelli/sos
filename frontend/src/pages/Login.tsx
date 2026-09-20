import { useState } from "react";
import { useNavigate } from "react-router";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!email.includes("@") || password.length < 4) {
      setError("Enter a valid email and a password of 4+ characters.");
      return;
    }
    // Level 8 will POST /api/auth/login and store the JWT. For now, enter the shell.
    setError("");
    navigate("/");
  };

  const field =
    "w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-600";

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6 pt-10">
      <div className="text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-red-600 text-2xl font-black text-white">
          S
        </span>
        <h2 className="mt-3 text-2xl font-extrabold">Operator sign in</h2>
        <p className="mt-1 text-sm text-slate-500">Security officers and admins only.</p>
      </div>
      <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500" htmlFor="email">
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
        <label
          className="mb-1 mt-4 block text-xs font-bold uppercase tracking-wide text-slate-500"
          htmlFor="password"
        >
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
        {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">{error}</p>}
        <button
          type="submit"
          className="mt-5 w-full rounded-lg bg-slate-900 py-2.5 text-sm font-bold text-white hover:bg-slate-800"
        >
          Sign In
        </button>
        <p className="mt-3 text-center text-xs text-slate-400">JWT auth wiring lands in Level 8.</p>
      </form>
    </div>
  );
}
