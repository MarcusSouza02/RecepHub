"use client";

import { useEffect, useState } from "react";
import { checkApi } from "@/services/api";

type Status = "loading" | "online" | "offline";

export function ApiStatus() {
  const [status, setStatus] = useState<Status>("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    checkApi(controller.signal)
      .then(() => { if (active) setStatus("online"); })
      .catch(() => { if (active) setStatus("offline"); })
      .finally(() => window.clearTimeout(timeout));
    return () => {
      active = false;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [attempt]);

  const labels = {
    loading: "Verificando conexão…",
    online: "API e banco de dados disponíveis",
    offline: "Não foi possível conectar ao sistema",
  };

  return (
    <div className="space-y-5">
      <p role="status" aria-live="polite" className="flex items-center gap-3 text-sm font-medium">
        <span aria-hidden="true" className={`size-2.5 shrink-0 rounded-full ${status === "online" ? "bg-emerald-600" : status === "offline" ? "bg-amber-600" : "animate-pulse bg-slate-400"}`} />
        {labels[status]}
      </p>
      {status === "offline" && <p className="text-sm leading-6 text-muted-foreground">Confira se os serviços estão em execução e tente novamente.</p>}
      <button
        type="button"
        disabled={status === "loading"}
        onClick={() => { setStatus("loading"); setAttempt((value) => value + 1); }}
        className="rounded-lg border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary disabled:cursor-wait disabled:opacity-50"
      >Verificar novamente</button>
    </div>
  );
}
