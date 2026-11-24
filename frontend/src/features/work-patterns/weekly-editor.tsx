"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "@/services/operations";
import { Alert, Button, Field, Input, controlClass, secondaryClass } from "@/components/ui/operations";
import { dayError, dayNames, duration, editableDay, hours, timeFields, type DayState, type PatternDay, type WeeklyPattern } from "./types";

function message(error: unknown) {
  return error instanceof ApiError ? error.status === 422
    ? "Revise os horários: entrada e saída devem ocorrer no mesmo dia, com intervalo contido na jornada."
    : error.message : "Não foi possível conectar. Tente novamente.";
}

export function WeeklyEditor({ employeeId }: { employeeId: string }) {
  return <Editor key={employeeId} employeeId={employeeId} />;
}

function Editor({ employeeId }: { employeeId: string }) {
  const [days, setDays] = useState<PatternDay[] | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [source, setSource] = useState(0);
  const [targets, setTargets] = useState<number[]>([]);
  const lock = useRef(false);
  const path = `/employees/${encodeURIComponent(employeeId)}/work-patterns`;

  useEffect(() => {
    const controller = new AbortController();
    api<WeeklyPattern>(path, { signal: controller.signal }).then(result => {
      if (!controller.signal.aborted) {
        setDays(result.days.map(editableDay).sort((a, b) => a.weekday - b.weekday));
        setError("");
      }
    }).catch(error => { if (!controller.signal.aborted) setError(message(error)); });
    return () => controller.abort();
  }, [path, reload]);

  function changeDay(weekday: number, changes: Partial<PatternDay>) {
    setDays(current => current?.map(day => day.weekday === weekday ? { ...day, ...changes } : day) || null);
    setDirty(true); setNotice(""); setError("");
  }
  function changeState(day: PatternDay, state: DayState) {
    changeDay(day.weekday, { state, ...(state !== "working" ? {
      start_time: null, end_time: null, break_start_time: null, break_end_time: null,
    } : {}) });
  }
  function repeat() {
    const origin = days?.find(day => day.weekday === source);
    if (!origin || !targets.length || lock.current) return;
    setDays(current => current?.map(day => targets.includes(day.weekday) ? { ...origin, weekday: day.weekday } : day) || null);
    setDirty(true); setError("");
    setNotice(`Configuração de ${dayNames[source]} copiada para ${targets.map(day => dayNames[day]).join(", ")}. Salve para confirmar.`);
    setTargets([]);
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!days || lock.current) return;
    const invalid = days.find(day => dayError(day));
    if (invalid) { setError(`${dayNames[invalid.weekday]}: ${dayError(invalid)}`); return; }
    lock.current = true; setBusy(true); setError(""); setNotice("");
    try {
      const result = await api<WeeklyPattern>(path, { method: "PUT", body: JSON.stringify({ days }) });
      setDays(result.days.map(editableDay).sort((a, b) => a.weekday - b.weekday));
      setDirty(false);
      setNotice(result.is_complete ? "Horários habituais salvos. Semana completa." : "Rascunho salvo. Há dias pendentes ou horários incompletos.");
    } catch (error) { setError(message(error)); }
    finally { lock.current = false; setBusy(false); }
  }
  const durations = days?.map(duration) || [];
  const subtotal = durations.reduce<number>((sum, value) => sum + (value ?? 0), 0);
  const complete = durations.length === 7 && durations.every(value => value !== null);

  return <section className="rounded-2xl border border-border bg-card p-4 sm:p-6" aria-labelledby={`weekly-${employeeId}`}>
    <h2 id={`weekly-${employeeId}`} className="text-lg font-semibold">Horários habituais</h2>
    <p className="mt-2 text-sm leading-6 text-muted-foreground">Configure os sete dias da semana. Horários incompletos podem ser salvos como rascunho. Use entrada e saída no mesmo dia; o intervalo é opcional.</p>
    <div className="mt-4" aria-live="polite">{notice && <p role="status" className="rounded-xl bg-muted p-3 text-sm">{notice}</p>}</div>
    {error && <div className="my-4"><Alert>{error}{!days && <button type="button" className="ml-2 underline" onClick={() => { setError(""); setReload(value => value + 1); }}>Tentar novamente</button>}</Alert></div>}
    {!days ? !error && <p role="status" className="py-8">Carregando horários habituais…</p> : <form onSubmit={save} aria-busy={busy} className="mt-5 space-y-5">
      <fieldset disabled={busy} className="min-w-0 space-y-4">
        <legend className="sr-only">Configuração de cada dia</legend>
        {days.map(day => {
          const invalid = dayError(day); const minutes = duration(day); const prefix = `weekly-${employeeId}-${day.weekday}`;
          return <fieldset key={day.weekday} className="min-w-0 rounded-xl border border-border p-4">
            <legend className="px-2 font-semibold">{dayNames[day.weekday]}</legend>
            <div className="grid items-end gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <Field id={`${prefix}-state`} label="Situação"><select id={`${prefix}-state`} className={controlClass} value={day.state} onChange={event => changeState(day, event.target.value as DayState)}><option value="pending">Pendente</option><option value="working">Com jornada</option><option value="non_working">Sem jornada</option></select></Field>
              {day.state === "working" && timeFields.map(field => <Field key={field.key} id={`${prefix}-${field.key}`} label={field.label}><Input id={`${prefix}-${field.key}`} type="time" step={60} value={day[field.key] || ""} aria-describedby={invalid ? `${prefix}-error` : undefined} aria-invalid={Boolean(invalid)} onChange={event => changeDay(day.weekday, { [field.key]: event.target.value || null })} /></Field>)}
            </div>
            {invalid ? <p id={`${prefix}-error`} className="mt-3 text-sm text-red-800">{invalid}</p> : <p className="mt-3 text-sm text-muted-foreground">{day.state === "pending" ? "Configuração pendente" : day.state === "non_working" ? "Sem jornada habitual · 0h 00min" : minutes === null ? "Jornada incompleta · não incluída no subtotal" : `Duração prevista: ${hours(minutes)}`}</p>}
          </fieldset>;
        })}
      </fieldset>
      <fieldset disabled={busy} className="min-w-0 space-y-4 rounded-xl border border-border p-4">
        <legend className="px-2 font-semibold">Repetir configuração</legend>
        <p className="text-sm text-muted-foreground">Copie a situação e todos os horários do dia de origem. Os dias escolhidos serão substituídos ao aplicar; salve a semana para confirmar.</p>
        <div className="max-w-sm"><Field id={`copy-source-${employeeId}`} label="Dia de origem"><select id={`copy-source-${employeeId}`} className={controlClass} value={source} onChange={event => { const next = Number(event.target.value); setSource(next); setTargets(current => current.filter(day => day !== next)); }}>{dayNames.map((name, day) => <option key={day} value={day}>{name}</option>)}</select></Field></div>
        <fieldset><legend className="mb-2 text-sm font-semibold">Copiar para</legend><div className="flex flex-wrap gap-x-5 gap-y-2">{dayNames.map((name, day) => day !== source && <label key={day} className="flex min-h-11 items-center gap-2 text-sm"><input type="checkbox" className="size-4 accent-primary" checked={targets.includes(day)} onChange={event => setTargets(current => event.target.checked ? [...current, day] : current.filter(value => value !== day))} />{name}</label>)}</div></fieldset>
        <button type="button" className={secondaryClass} disabled={busy || !targets.length} onClick={repeat}>Aplicar aos dias escolhidos</button>
      </fieldset>
      <div className="rounded-xl bg-muted p-4 text-sm" aria-live="polite"><p className="font-semibold">{complete ? `Total semanal previsto: ${hours(subtotal)}` : "Total semanal indisponível: semana incompleta"}</p><p className="mt-1">Subtotal dos dias completos: {hours(subtotal)}</p><p className="mt-2 text-muted-foreground">Estimativa aritmética dos horários habituais. Não representa ponto ou validação de jornada contratual.</p></div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5"><p className="text-sm text-muted-foreground">{dirty ? "Há alterações ainda não salvas." : "Nenhuma alteração pendente."}</p><Button type="submit" disabled={busy || !dirty}>{busy ? "Salvando…" : "Salvar horários habituais"}</Button></div>
    </form>}
  </section>;
}
