"use client";
import {useState, type FormEvent} from "react";

export type Account = {id: string; email: string | null; displayName: string; method: "session" | "chatgpt"};

async function authRequest(path: string, body?: Record<string, string>) {
  const r = await fetch(path, {
    method: body ? "POST" : "GET",
    credentials: "include",
    cache: "no-store",
    headers: body ? {"Content-Type": "application/json"} : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json() as Account & {error?: string};
  if (!r.ok) throw new Error(data.error ?? "Could not complete sign-in.");
  return data;
}

export function AuthPanel({onSignedIn}: {onSignedIn: (account: Account) => void}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    setBusy(true); setError("");
    try {
      onSignedIn(await authRequest(mode === "register" ? "/api/auth/register" : "/api/auth/login", values));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not complete sign-in.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="sh-panel sh-auth-panel">
      <header><h2>{mode === "register" ? "Create organizer account" : "Sign in to your workspace"}</h2></header>
      <p className="sh-method">Email and password are stored on this host. ChatGPT Sites sign-in still works when this app is served from that dispatcher.</p>
      <form className="sh-room-form" onSubmit={submit}>
        {mode === "register" && <label>Display name<input name="displayName" autoComplete="name" required maxLength={80} disabled={busy}/></label>}
        <label>Email<input name="email" type="email" autoComplete="email" required disabled={busy}/></label>
        <label>Password<input name="password" type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} minLength={10} required disabled={busy}/></label>
        {error && <div className="sh-error" role="alert"><p>{error}</p></div>}
        <button className="sh-primary" disabled={busy}>{busy ? "Please wait…" : mode === "register" ? "Create account" : "Sign in"}</button>
      </form>
      <button className="sh-button" disabled={busy} onClick={() => { setMode(mode === "register" ? "login" : "register"); setError(""); }}>
        {mode === "register" ? "Already have an account" : "Create an organizer account"}
      </button>
      <a href="/signin-with-chatgpt?return_to=%2F" target="_top">Sign in with ChatGPT</a>
    </section>
  );
}

export function AccountChip({account, onSignedOut}: {account: Account | null; onSignedOut: () => void}) {
  const [busy, setBusy] = useState(false);
  if (!account) return null;
  return (
    <div className="sh-account">
      <span>{account.displayName}</span>
      {account.method === "session" && (
        <button className="sh-button" disabled={busy} onClick={async () => {
          setBusy(true);
          try {
            await fetch("/api/auth/logout", {method: "POST", credentials: "include"});
            onSignedOut();
          } finally {
            setBusy(false);
          }
        }}>{busy ? "Signing out…" : "Sign out"}</button>
      )}
    </div>
  );
}
