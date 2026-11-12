"use client";
import { useEffect, useState } from "react";
export function SessionMonitor({ expiresAt, idleExpiresAt, serverNow }: { expiresAt: string; idleExpiresAt: string; serverNow: number }) {
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let disposed = false, inFlight = false;
    let deadline = performance.now() + Math.min(Date.parse(expiresAt), Date.parse(idleExpiresAt)) - serverNow;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    function expire() { if (!disposed) window.location.replace("/login"); }
    function schedule() {
      clearTimeout(timer);
      if (!Number.isFinite(deadline)) { setUnavailable(true); return; }
      const remaining = deadline - performance.now();
      if (remaining <= 0) { expire(); return; }
      // No polling: an idle tab must not renew its own session.
      timer = setTimeout(expire, remaining);
    }
    async function revalidate() {
      if (disposed || inFlight || document.visibilityState !== "visible") return;
      if (performance.now() >= deadline) { expire(); return; }
      inFlight = true;
      try {
        const response = await fetch("/api/v1/auth/session", { credentials: "same-origin", cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(5000)]) });
        if (disposed) return;
        if (response.status === 401) { expire(); return; }
        if (!response.ok) { setUnavailable(true); return; }
        const value = await response.json();
        const serverDate = Date.parse(response.headers.get("date") ?? "");
        const updated = performance.now() + Math.min(Date.parse(value.expires_at), Date.parse(value.idle_expires_at)) - serverDate;
        if (!Number.isFinite(updated)) { setUnavailable(true); return; }
        deadline = updated; setUnavailable(false); schedule();
      } catch { if (!disposed) setUnavailable(true); }
      finally { inFlight = false; }
    }
    function onVisible() { if (document.visibilityState === "visible") void revalidate(); }
    function onPageShow(event: PageTransitionEvent) { if (event.persisted) void revalidate(); }
    schedule();
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", revalidate);
    window.addEventListener("pageshow", onPageShow);
    return () => { disposed = true; controller.abort(); clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", revalidate); window.removeEventListener("pageshow", onPageShow); };
  }, [expiresAt, idleExpiresAt, serverNow]);
  return unavailable ? <p role="status" className="border-b border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 md:ml-64">Não foi possível verificar sua sessão. Confira sua conexão e tente novamente.</p> : null;
}
