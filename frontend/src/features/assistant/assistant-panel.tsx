"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Alert, Button, ConfirmDialog, Field, Input, controlClass } from "@/components/ui/operations";
import { api, ApiError } from "@/services/operations";
import type { Assignment, Schedule } from "@/features/schedules/types";

export type AssistantStatus = { enabled: boolean; provider: string; external_data: boolean; proposals_enabled: boolean };
function ScheduleReferences({ schedule }: { schedule: Schedule }) {
  return <details className="rounded-xl border border-border p-4"><summary className="cursor-pointer font-semibold">Referências desta escala</summary><p className="my-3 text-sm text-muted-foreground">Copie os identificadores completos no pedido para distinguir nomes iguais. Para outras unidades, consulte os detalhes no cadastro de unidades.</p><ul className="space-y-3">{schedule.days.map(day => <li key={day.id} className="space-y-1 border-t border-border pt-3 text-sm"><p>{day.employee_name} · {day.work_date}</p><p className="break-all">Pessoa: {day.employee_id}</p><p className="break-all">Dia: {day.id}</p>{day.assignments.map(row => <div key={row.id}><p className="break-all">Unidade {row.unit_name}: {row.unit_id}</p><p className="break-all">Alocação: {row.id}</p></div>)}</li>)}</ul></details>;
}
type Preview = { status: "ready" | "needs_clarification" | "blocked"; message: string; differences: { day_id: string; before: Assignment[]; after: Assignment[] }[]; impediments: string[]; receipt: string | null; expires_in: number };
function periods(rows: Assignment[]) {
  return rows.length ? rows.map(row => {
    const pause = row.break_start_time || row.break_end_time
      ? `Intervalo: ${row.break_start_time?.slice(0, 5) ?? "início não informado"}–${row.break_end_time?.slice(0, 5) ?? "fim não informado"}`
      : "Sem intervalo";
    return `Unidade: ${row.unit_name} (${row.unit_id.slice(0, 8)}) · Entrada: ${row.start_time.slice(0, 5)} · Saída: ${row.end_time.slice(0, 5)} · ${pause} · Atividade: ${row.position || "Sem atividade"}`;
  }).join("; ") : "Sem períodos";
}

export function AssistantPanel({ schedule, onUpdated }: { schedule: Schedule; onUpdated: (schedule: Schedule) => void }) {
  const [status, setStatus] = useState<AssistantStatus | null>(null); const [statusError, setStatusError] = useState(""); const [reload, setReload] = useState(0);
  const [request, setRequest] = useState(""); const [reference, setReference] = useState(() => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date()));
  const [consent, setConsent] = useState(false); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const lock = useRef(false);
  const [proposal, setProposal] = useState<{ data: Preview; key: string; expires: number } | null>(null); const [confirm, setConfirm] = useState(false);
  const key = JSON.stringify([schedule.id, schedule.version, request, reference, consent]);
  const current = proposal?.key === key ? proposal : null;
  useEffect(() => { const controller = new AbortController(); api<AssistantStatus>("/assistant/status", { signal: controller.signal }).then(data => { if (!controller.signal.aborted) { setStatus(data); setStatusError(""); } }).catch(() => { if (!controller.signal.aborted) setStatusError("Não foi possível consultar a assistência opcional."); }); return () => controller.abort(); }, [reload]);
  async function preview(event: FormEvent) {
    event.preventDefault(); if (lock.current) return; lock.current = true; setBusy(true); setError(""); setProposal(null);
    try { const data = await api<Preview>(`/schedules/${schedule.id}/proposals/preview`, { method: "POST", body: JSON.stringify({ expected_version: schedule.version, request, reference_date: reference, consent_external: consent }) }); setProposal({ data, key, expires: Date.now() + data.expires_in * 1000 }); }
    catch (error) { setError(error instanceof ApiError ? error.status === 409 ? "A escala mudou. Seu pedido foi preservado; recarregue a escala e gere uma nova prévia." : error.message : "Não foi possível gerar a prévia. Tente novamente."); }
    finally { lock.current = false; setBusy(false); }
  }
  async function apply() {
    if (!current?.data.receipt || lock.current) return;
    if (Date.now() >= current.expires) { setError("A prévia expirou. Gere outra antes de confirmar."); setProposal(null); setConfirm(false); return; }
    lock.current = true; setBusy(true); setError("");
    try { const result = await api<Schedule>(`/schedules/${schedule.id}/proposals/confirm`, { method: "POST", body: JSON.stringify({ receipt: current.data.receipt, confirmed: true }) }); setProposal(null); onUpdated(result); }
    catch (error) { setProposal(null); setError(error instanceof ApiError ? error.status === 409 ? "A escala ou as condições mudaram. Seu pedido foi preservado. Gere outra prévia após recarregar." : error.message : "Não foi possível confirmar. Recarregue antes de tentar novamente."); }
    finally { lock.current = false; setBusy(false); setConfirm(false); }
  }
  return <section aria-label="Assistência opcional" className="space-y-4 rounded-2xl border border-border bg-card p-5"><h2 className="text-xl font-semibold">Assistência opcional</h2>{statusError ? <Alert>{statusError} <button className="underline" onClick={() => setReload(value => value + 1)}>Tentar novamente</button></Alert> : !status ? <p role="status">Consultando disponibilidade…</p> : !status.enabled || !status.proposals_enabled ? <p>A assistência está desativada. A edição manual, os comunicados e as exportações continuam disponíveis.</p> : <><p className="text-sm text-muted-foreground">A prévia não altera a escala. A confirmação modifica somente o conteúdo corrente, sem publicar.</p><ScheduleReferences schedule={schedule} /><form onSubmit={preview} className="space-y-4"><Field id="assistant-request" label="Pedido para a escala" hint="Até 1000 caracteres. Identifique pessoas, unidades, dias e horários."><textarea id="assistant-request" required maxLength={1000} className={controlClass} rows={4} value={request} disabled={busy} onChange={event => setRequest(event.target.value)} /></Field><Field id="assistant-reference" label="Data de referência" hint="Data local de São Paulo usada para interpretar hoje e amanhã."><Input id="assistant-reference" required type="date" value={reference} disabled={busy} onChange={event => setReference(event.target.value)} /></Field>{status.external_data && <label className="flex gap-3 text-sm"><input type="checkbox" checked={consent} disabled={busy} onChange={event => setConsent(event.target.checked)} />Autorizo enviar este pedido e o contexto mínimo ao provedor externo.</label>}<Button disabled={busy || (status.external_data && !consent)} type="submit">{busy ? "Processando…" : "Gerar prévia"}</Button></form></>}{error && <Alert>{error}</Alert>}{current && <div className="space-y-4"><p role="status">{current.data.message}</p>{current.data.impediments.map((item, index) => <p key={index} className="text-sm text-red-800">{item}</p>)}{current.data.differences.map((difference, index) => { const day = schedule.days.find(day => day.id === difference.day_id); return <article key={`${difference.day_id}-${index}`} className="space-y-2 rounded-xl border border-border p-4"><h3 className="font-semibold" title={day?.employee_id}>{day?.employee_name ?? "Colaboradora"} ({day?.employee_id.slice(0, 8) ?? "sem ID"}) · {day?.work_date ?? "Data não identificada"}</h3><p className="break-all text-xs">Dia: {difference.day_id}</p><p className="break-words text-sm" title={difference.before.map(row => row.unit_id).join(", ")}>Antes: {periods(difference.before)}</p><p className="break-words text-sm" title={difference.after.map(row => row.unit_id).join(", ")}>Depois: {periods(difference.after)}</p></article>; })}{current.data.status === "ready" && current.data.receipt && <Button disabled={busy} onClick={() => setConfirm(true)}>Revisar e confirmar proposta</Button>}</div>}{confirm && current && <ConfirmDialog title="Aplicar proposta ao rascunho?" busy={busy} onCancel={() => setConfirm(false)} onConfirm={apply}>Confira as diferenças acima. O servidor validará novamente a versão e os impedimentos. Esta ação não publica a escala.</ConfirmDialog>}</section>;
}
