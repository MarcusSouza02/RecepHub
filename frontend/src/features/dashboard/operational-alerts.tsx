"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { Alert, Button, Field, Input } from "@/components/ui/operations";
import { api } from "@/services/operations";

type Result = {
  from_date: string; to_date: string;
  active_absences: { total: number; truncated: boolean; items: { id: string; employee_name: string; start_date: string; end_date: string; href: string }[] };
  current_assignment_conflicts: { total: number; truncated: boolean; items: { assignment_id: string; employee_name: string; work_date: string; href: string }[] };
};
const localDate = (date: Date) => {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date);
  return ["year", "month", "day"].map(type => parts.find(part => part.type === type)!.value).join("-");
};
const label = (value: string) => value.split("-").reverse().join("/");

export function OperationalAlerts() {
  const [initial] = useState(() => { const from = localDate(new Date()); const end = new Date(`${from}T12:00:00Z`); end.setUTCDate(end.getUTCDate() + 6); return { from, to: end.toISOString().slice(0, 10) }; });
  const [from, setFrom] = useState(initial.from), [to, setTo] = useState(initial.to);
  const [period, setPeriod] = useState(initial), [attempt, setAttempt] = useState(0);
  const [data, setData] = useState<Result | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    void api<Result>(`/dashboard/operational-alerts?${new URLSearchParams({ from_date: period.from, to_date: period.to })}`, { signal: controller.signal }).then(result => {
      if (!controller.signal.aborted) { setData(result); setLoading(false); setError(""); }
    }).catch(error => { if (!controller.signal.aborted) { setError(error instanceof Error ? error.message : "Não foi possível consultar os alertas."); setLoading(false); } });
    return () => controller.abort();
  }, [period, attempt]);
  function submit(event: FormEvent) { event.preventDefault(); setLoading(true); setError(""); setPeriod({ from, to }); }
  return <section aria-labelledby="operational-alerts-title" className="space-y-4 rounded-2xl border border-border bg-card p-5">
    <h2 id="operational-alerts-title" className="text-xl font-semibold">Ausências e impedimentos</h2>
    <p className="text-sm text-muted-foreground">Ausências ativas e alocações correntes afetadas no período consultado. Não representa presença nem cobertura mínima.</p>
    <form onSubmit={submit} className="flex flex-wrap items-end gap-4">
      <Field id="alerts-from" label="Alertas a partir de"><Input id="alerts-from" type="date" required value={from} onChange={event => setFrom(event.target.value)} /></Field>
      <Field id="alerts-to" label="Alertas até"><Input id="alerts-to" type="date" required min={from} value={to} onChange={event => setTo(event.target.value)} /></Field>
      <Button disabled={loading}>Consultar alertas</Button>
    </form>
    {loading ? <p role="status">Carregando alertas…</p> : error ? <div className="space-y-3"><Alert>{error}</Alert><Button onClick={() => { setLoading(true); setError(""); setAttempt(value => value + 1); }}>Tentar novamente</Button></div> : data && <div className="space-y-4">
      <p className="text-sm">Período: {label(data.from_date)} a {label(data.to_date)}</p>
      <div className="grid gap-5 md:grid-cols-2"><div><h3 className="font-semibold">Ausências ativas: {data.active_absences.total}</h3>
        {data.active_absences.total === 0 ? <p className="mt-2 text-sm">Nenhuma ausência ativa neste período.</p> : <ul className="mt-2 space-y-2">{data.active_absences.items.map(item => <li key={item.id}><Link className="text-sm underline" href={item.href}>{item.employee_name}: {label(item.start_date)} a {label(item.end_date)}</Link></li>)}</ul>}
        {data.active_absences.truncated && <p className="mt-2 text-sm">Exibindo as primeiras 20 ausências. <Link href="/absences" className="underline">Consultar cadastro</Link></p>}
      </div><div><h3 className="font-semibold">Alocações com ausência: {data.current_assignment_conflicts.total}</h3>
        {data.current_assignment_conflicts.total === 0 ? <p className="mt-2 text-sm">Nenhuma alocação corrente em conflito com ausência neste período.</p> : <ul className="mt-2 space-y-2">{data.current_assignment_conflicts.items.map(item => <li key={item.assignment_id}><Link className="text-sm underline" href={item.href}>{item.employee_name}: {label(item.work_date)} — revisar escala</Link></li>)}</ul>}
        {data.current_assignment_conflicts.truncated && <p className="mt-2 text-sm">Exibindo as primeiras 20 alocações afetadas. <Link href="/schedules" className="underline">Consultar escalas</Link></p>}
      </div></div>
    </div>}
  </section>;
}
