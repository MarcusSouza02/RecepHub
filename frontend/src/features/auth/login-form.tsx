"use client";
import { useRef, useState, type FormEvent } from "react";
export function LoginForm() {
  const active = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (active.current) return;
    active.current = true;
    const data = new FormData(event.currentTarget);
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/v1/auth/login", { method: "POST", credentials: "same-origin", cache: "no-store",
        headers: { "Content-Type": "application/json", "X-RecepHub-CSRF": "1" },
        body: JSON.stringify({ username: data.get("username"), password: data.get("password") }) });
      if (response.ok) { window.location.replace("/dashboard"); return; }
      setError(response.status === 429 ? "Muitas tentativas. Aguarde e tente novamente." : response.status >= 500 ? "Serviço indisponível. Tente novamente em instantes." : response.status === 422 ? "Confira o usuário e a senha informados." : "Usuário ou senha inválidos.");
    } catch { setError("Não foi possível conectar. Tente novamente."); }
    finally { setBusy(false); active.current = false; }
  }
  const field = "mt-2 min-h-12 w-full rounded-xl border border-border bg-white px-4 py-3 outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-60";
  return <form onSubmit={submit} aria-busy={busy} className="mt-8 space-y-5">
    <div><label htmlFor="username" className="text-sm font-semibold">Usuário</label><input id="username" name="username" autoComplete="username" autoCapitalize="none" spellCheck={false} required minLength={3} maxLength={80} disabled={busy} className={field} /></div>
    <div><label htmlFor="password" className="text-sm font-semibold">Senha</label><input id="password" name="password" type="password" autoComplete="current-password" required minLength={15} maxLength={128} disabled={busy} className={field} /></div>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}
    <button disabled={busy} className="min-h-12 w-full rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary disabled:opacity-60">{busy ? "Entrando…" : "Entrar"}</button>
    <p role="status" className="sr-only">{busy ? "Verificando suas credenciais" : ""}</p>
  </form>;
}
