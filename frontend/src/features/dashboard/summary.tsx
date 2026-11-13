"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Alert, Button } from "@/components/ui/operations";
import { api } from "@/services/operations";

type Summary = {
  active_units: number;
  active_employees: number;
  active_employees_without_home_unit: number;
};

export function DashboardSummary() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const load = async (signal?: AbortSignal) => {
    try {
      const result = await api<Summary>("/dashboard/summary", { signal });
      if (!signal?.aborted) setSummary(result);
    } catch {
      if (!signal?.aborted) setError(true);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  };
  useEffect(() => {
    const controller = new AbortController();
    api<Summary>("/dashboard/summary", { signal: controller.signal }).then(result => {
      if (!controller.signal.aborted) { setSummary(result); setLoading(false); }
    }).catch(() => {
      if (!controller.signal.aborted) { setError(true); setLoading(false); }
    });
    return () => controller.abort();
  }, []);

  if (loading) return <p role="status" className="mt-8 text-sm text-muted-foreground">Carregando indicadores…</p>;
  if (error || !summary) return <div className="mt-8 space-y-4"><Alert>Não foi possível carregar os indicadores. Tente novamente.</Alert><Button onClick={() => { setLoading(true); setError(false); void load(); }}>Tentar novamente</Button></div>;

  const cards = [
    { label: "Unidades ativas", value: summary.active_units, href: "/units", detail: "Locais disponíveis para novos vínculos" },
    { label: "Colaboradoras ativas", value: summary.active_employees, href: "/employees", detail: "Pessoas com cadastro ativo" },
    { label: "Ativas sem unidade habitual", value: summary.active_employees_without_home_unit, href: "/employees", detail: "Cadastros que podem receber um vínculo" },
  ];
  return <section aria-label="Indicadores operacionais" className="mt-8 grid gap-4 md:grid-cols-3">
    {cards.map(card => <Link key={card.label} href={card.href} className="rounded-[18px] border border-border bg-card p-6 shadow-sm transition hover:border-primary focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary">
      <h2 className="text-sm font-medium text-muted-foreground">{card.label}</h2>
      <p className="mt-3 text-4xl font-semibold tracking-tight tabular-nums">{card.value}</p>
      <p className="mt-3 text-xs leading-5 text-muted-foreground">{card.detail}</p>
    </Link>)}
  </section>;
}
