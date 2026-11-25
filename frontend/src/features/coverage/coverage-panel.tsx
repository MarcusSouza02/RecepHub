"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Alert, Button, ConfirmDialog, Field, Input, controlClass, secondaryClass } from "@/components/ui/operations";
import { api, ApiError } from "@/services/operations";
import type { Schedule, ScheduleDay, Unit } from "@/features/schedules/types";

type Intent = { expected_version: number; work_date: string; unit_id: string; start_time: string; end_time: string; position: string | null };
type Candidate = { employee_id: string; employee_name: string; classification: "available" | "unavailable" | "insufficient_information"; reasons: { code: string; message: string }[]; known_periods: { start_time: string; end_time: string }[] };
type Preview = { expected_version: number; request: Intent; candidates: Candidate[] };
const labels = { available: "Disponível", unavailable: "Indisponível", insufficient_information: "Informação insuficiente" };
const errorMessage = (error: unknown) => error instanceof ApiError && error.status === 409 ? "Os dados mudaram ou existe um impedimento. Seu formulário foi preservado. Recarregue a escala e consulte novamente antes de confirmar." : error instanceof Error ? error.message : "Não foi possível consultar a cobertura.";

export function CoveragePanel({ scheduleId, version, days, onUpdated }: { scheduleId: string; version: number; days: ScheduleDay[]; onUpdated: (schedule: Schedule) => void }) {
  const [unitsAttempt, setUnitsAttempt] = useState(0);
  const [units, setUnits] = useState<Unit[]>([]), [loadingUnits, setLoadingUnits] = useState(true);
  const [workDate, setWorkDate] = useState(days[0]?.work_date ?? ""), [unitId, setUnitId] = useState("");
  const [start, setStart] = useState(""), [end, setEnd] = useState(""), [position, setPosition] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null), [selected, setSelected] = useState<Candidate | null>(null);
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [success, setSuccess] = useState("");
  const dates = [...new Set(days.map(day => day.work_date))].sort();
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const result: Unit[] = [];
      let page = 1, total = 0;
      do {
        const response = await api<{ items: Unit[]; total: number }>(`/units?status=active&page=${page}&page_size=100`, { signal: controller.signal });
        result.push(...response.items); total = response.total; page++;
        if (response.items.length === 0) break;
      } while (result.length < total);
      if (!controller.signal.aborted) { setUnits(result); setLoadingUnits(false); }
    }
    void load().catch(error => { if (!controller.signal.aborted) { setError(errorMessage(error)); setLoadingUnits(false); } });
    return () => controller.abort();
  }, [unitsAttempt]);
  function change(action: () => void) { action(); setPreview(null); setSelected(null); setSuccess(""); }
  async function consult(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setSuccess(""); setPreview(null);
    const intent: Intent = { expected_version: version, work_date: workDate, unit_id: unitId, start_time: start, end_time: end, position: position || null };
    try { setPreview(await api<Preview>(`/schedules/${scheduleId}/coverage/preview`, { method: "POST", body: JSON.stringify(intent) })); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  async function confirm() {
    if (!selected || !preview || preview.expected_version !== version || busy) return;
    setBusy(true); setError("");
    try {
      const updated = await api<Schedule>(`/schedules/${scheduleId}/coverage/confirm`, { method: "POST", body: JSON.stringify({ ...preview.request, employee_id: selected.employee_id, confirmed: true }) });
      setSelected(null); setPreview(null); setSuccess("Cobertura adicionada ao rascunho. Revise a alocação original e os impedimentos antes de publicar."); onUpdated(updated);
    } catch (error) { setSelected(null); setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <section aria-labelledby="coverage-title" className="space-y-4 rounded-2xl border border-border bg-card p-5">
    <h2 id="coverage-title" className="text-xl font-semibold">Consultar cobertura</h2>
    <p className="text-sm text-muted-foreground">Consulta manual pela jornada congelada na semana. A confirmação adiciona um período ao rascunho; a alocação original permanece para revisão.</p>
    {error && <Alert>{error}</Alert>}{!loadingUnits && units.length === 0 && <button type="button" className={secondaryClass} onClick={() => { setLoadingUnits(true); setError(""); setUnitsAttempt(value => value + 1); }}>Recarregar unidades</button>}{success && <p role="status">{success}</p>}
    <form onSubmit={consult} className="grid gap-4 sm:grid-cols-2">
      <Field id="coverage-date" label="Data da cobertura"><select id="coverage-date" required className={controlClass} disabled={busy} value={workDate} onChange={event => change(() => setWorkDate(event.target.value))}>{dates.map(date => <option key={date} value={date}>{date.split("-").reverse().join("/")}</option>)}</select></Field>
      <Field id="coverage-unit" label="Unidade da cobertura"><select id="coverage-unit" required className={controlClass} disabled={busy || loadingUnits} value={unitId} onChange={event => change(() => setUnitId(event.target.value))}><option value="">{loadingUnits ? "Carregando unidades…" : "Selecione uma unidade ativa"}</option>{units.map(unit => <option key={unit.id} value={unit.id}>{unit.name}</option>)}</select></Field>
      <Field id="coverage-start" label="Início da cobertura"><Input id="coverage-start" type="time" required disabled={busy} value={start} onChange={event => change(() => setStart(event.target.value))} /></Field>
      <Field id="coverage-end" label="Fim da cobertura"><Input id="coverage-end" type="time" required disabled={busy} value={end} onChange={event => change(() => setEnd(event.target.value))} /></Field>
      <Field id="coverage-position" label="Atividade da cobertura (opcional)"><Input id="coverage-position" maxLength={80} disabled={busy} value={position} onChange={event => change(() => setPosition(event.target.value))} /></Field>
      <div className="flex items-end"><Button disabled={busy || loadingUnits || dates.length === 0}>{busy ? "Consultando…" : "Consultar candidatas"}</Button></div>
    </form>
    {preview && <div className="space-y-3" aria-live="polite">
      {preview.expected_version !== version && <Alert>A versão da escala mudou. Consulte novamente antes de confirmar.</Alert>}
      {preview.candidates.length === 0 && <p>Nenhuma colaboradora cadastrada para consultar.</p>}
      {preview.candidates.map(candidate => <article key={candidate.employee_id} className="space-y-2 rounded-xl border border-border p-4">
        <h3 className="font-semibold">{candidate.employee_name}</h3><p>{labels[candidate.classification]}</p>
        {candidate.reasons.length > 0 && <ul className="list-inside list-disc text-sm">{candidate.reasons.map(reason => <li key={reason.code}>{reason.message}</li>)}</ul>}
        {candidate.known_periods.length > 0 && <p className="text-sm text-muted-foreground">Períodos conhecidos: {candidate.known_periods.map(period => `${period.start_time.slice(0, 5)}–${period.end_time.slice(0, 5)}`).join(", ")}</p>}
        {candidate.classification === "available" && <button className={secondaryClass} disabled={busy || preview.expected_version !== version} onClick={() => setSelected(candidate)}>Selecionar {candidate.employee_name}</button>}
      </article>)}
    </div>}
    {selected && <ConfirmDialog title="Confirmar cobertura no rascunho?" busy={busy} onCancel={() => setSelected(null)} onConfirm={() => void confirm()}>Adicionar {selected.employee_name} em {workDate.split("-").reverse().join("/")}, das {start} às {end}? A publicação exige outra confirmação.</ConfirmDialog>}
  </section>;
}
