"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Alert, Button, Field, Input, controlClass } from "@/components/ui/operations";
import { api } from "@/services/operations";
import { downloadExport } from "@/services/downloads";
import type { Revision, Schedule } from "@/features/schedules/types";

type Preview = { page_count: number; filename: string; layout_version: string };
export function ExportPanel({ schedule, revisions, revision }: { schedule: Schedule; revisions: Revision[]; revision: Revision | null }) {
  const initial = revision?.number ?? schedule.latest_revision_number;
  const [source, setSource] = useState(initial ? `revision:${initial}` : "");
  const [format, setFormat] = useState("pdf"), [page, setPage] = useState("1");
  const [unit, setUnit] = useState(""), [date, setDate] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null), [intent, setIntent] = useState("");
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [success, setSuccess] = useState("");
  const [historical, setHistorical] = useState<{ source: string; data?: Schedule; error?: string } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const number = Number(source.split(":")[1]);
  const shown = source === "draft" ? schedule : revision?.number === number ? revision.snapshot : historical?.source === source ? historical.data : undefined;
  useEffect(() => {
    if (!source.startsWith("revision:") || revision?.number === number) return;
    const controller = new AbortController();
    api<Revision>(`/schedules/${schedule.id}/revisions/${number}`, { signal: controller.signal }).then(value => { if (!controller.signal.aborted) setHistorical({ source, data: value.snapshot }); }).catch(() => { if (!controller.signal.aborted) setHistorical({ source, error: "Não foi possível carregar essa revisão para selecionar o recorte." }); });
    return () => controller.abort();
  }, [source, number, revision?.number, schedule.id, attempt]);
  const units = new Map((shown?.days ?? []).flatMap(day => day.assignments.map(a => [a.unit_id, a.unit_name] as const)));
  const payload = {
    source: source === "draft" ? { kind: "draft", expected_version: schedule.version } : { kind: "revision", revision_number: Number(source.split(":")[1]) },
    format, ...(unit ? { unit_id: unit } : {}), ...(date ? { work_date: date } : {}),
  };
  const currentIntent = JSON.stringify(payload);
  async function consult(event: FormEvent) {
    event.preventDefault(); if (busy) return; setBusy(true); setError(""); setSuccess(""); setPreview(null);
    try { const result = await api<Preview>(`/schedules/${schedule.id}/exports/preview`, { method: "POST", body: currentIntent }); setPreview(result); setIntent(currentIntent); setPage("1"); }
    catch (error) { setError(error instanceof Error ? error.message : "Não foi possível preparar a exportação."); }
    finally { setBusy(false); }
  }
  async function download() {
    if (busy || !preview || intent !== currentIntent) return; setBusy(true); setError(""); setSuccess("");
    try { await downloadExport(schedule.id, { ...payload, ...(format === "png" ? { page: Number(page) } : {}) }); setSuccess("Arquivo preparado para download."); }
    catch (error) { setError(error instanceof Error ? error.message : "Não foi possível baixar."); }
    finally { setBusy(false); }
  }
  return <section aria-labelledby="export-heading" className="space-y-4 rounded-2xl border border-border bg-card p-5">
    <h2 id="export-heading" className="text-xl font-semibold">Exportar escala</h2>
    <p className="text-sm text-muted-foreground">PDF com texto selecionável ou PNG por página. A exportação não publica nem envia a escala.</p>
    <form onSubmit={consult} className="grid gap-4 sm:grid-cols-2">
      <Field id="export-source" label="Versão para exportação"><select id="export-source" required className={controlClass} value={source} onChange={e => { setSource(e.target.value); setUnit(""); setDate(""); setPreview(null); }}><option value="">Selecione explicitamente</option>{revisions.map(r => <option key={r.number} value={`revision:${r.number}`}>Publicada · revisão {r.number}</option>)}<option value="draft">Rascunho não publicado · versão {schedule.version}</option></select></Field>
      <Field id="export-format" label="Formato"><select id="export-format" className={controlClass} value={format} onChange={e => setFormat(e.target.value)}><option value="pdf">PDF</option><option value="png">PNG por página</option></select></Field>
      <Field id="export-unit" label="Unidade da exportação"><select id="export-unit" className={controlClass} value={unit} onChange={e => setUnit(e.target.value)}><option value="">Todas as unidades</option>{[...units].map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></Field>
      <Field id="export-date" label="Data da exportação"><select id="export-date" className={controlClass} value={date} onChange={e => setDate(e.target.value)}><option value="">Semana completa</option>{[...new Set((shown?.days ?? []).map(d => d.work_date))].sort().map(value => <option key={value} value={value}>{value.split("-").reverse().join("/")}</option>)}</select></Field>
      <Button disabled={busy || (!!source && !shown)}>{busy ? "Preparando…" : "Conferir exportação"}</Button>
    </form>
    {source === "draft" && <p className="text-sm font-semibold text-amber-900">Todas as páginas serão marcadas como RASCUNHO NÃO PUBLICADO.</p>}
    {error && <Alert>{error}</Alert>}{success && <p role="status">{success}</p>}
    {historical?.source === source && historical.error && <div><Alert>{historical.error}</Alert><Button type="button" onClick={() => setAttempt(value => value + 1)}>Recarregar revisão</Button></div>}
    {preview && intent === currentIntent && <div className="space-y-3"><p>{preview.page_count} página(s) · {preview.filename}</p>{format === "png" && <Field id="export-page" label="Página do PNG"><Input id="export-page" type="number" min={1} max={preview.page_count} value={page} onChange={e => setPage(e.target.value)} /></Field>}<Button type="button" disabled={busy || (format === "png" && (!Number.isInteger(Number(page)) || Number(page) < 1 || Number(page) > preview.page_count))} onClick={() => void download()}>Baixar {format.toUpperCase()}</Button></div>}
  </section>;
}
