"use client";
import { useState } from "react";
export function LogoutButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function logout() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/v1/auth/logout", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-RecepHub-CSRF": "1" }, body: "{}", cache: "no-store" });
      if (response.status === 204) { window.location.replace("/login"); return; }
      setError("Não foi possível sair. Tente novamente.");
    } catch { setError("Não foi possível conectar. Tente novamente."); }
    finally { setBusy(false); }
  }
  return <div><button type="button" disabled={busy} onClick={logout} className="min-h-11 rounded-xl border border-border px-5 py-2 text-sm font-semibold hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary disabled:opacity-60">{busy ? "Saindo…" : "Sair"}</button>{error && <p role="alert" className="mt-2 text-sm text-red-800">{error}</p>}</div>;
}
