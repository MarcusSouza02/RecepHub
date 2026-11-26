"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import type { AssistantStatus } from "@/features/assistant/assistant-panel";
import { Alert, Button, Field, Input, controlClass, secondaryClass } from "@/components/ui/operations";
import { api, ApiError } from "@/services/operations";

const labels = { publication: "Publicação de escala", schedule_update: "Atualização de escala", time_change: "Alteração de horário", unit_change: "Mudança de unidade", coverage: "Cobertura", notice: "Aviso geral" };
export type CommunicationContext = { scheduleId?: string; sourceKind?: "revision" | "draft"; sourceNumber?: number };

export function CommunicationsClient({ scheduleId, sourceKind, sourceNumber }: CommunicationContext) {
  const [type, setType] = useState<keyof typeof labels>("notice");
  const [subject, setSubject] = useState(""); const [body, setBody] = useState("");
  const [error, setError] = useState(""); const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false); const lock = useRef(false);
  const [generated, setGenerated] = useState(false);
  async function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (lock.current) return;
    lock.current = true; setBusy(true); setError(""); setFeedback("");
    const message = String(new FormData(event.currentTarget).get("message") || "");
    const source = sourceKind === "revision" ? { kind: "revision", revision_number: sourceNumber } : { kind: "draft", expected_version: sourceNumber };
    try {
      const result = await api<{ subject: string; body: string }>("/communications/prepare", { method: "POST", body: JSON.stringify({ type, message, ...(scheduleId ? { schedule_id: scheduleId, source } : {}) }) });
      setSubject(result.subject); setBody(result.body); setGenerated(true);
    } catch (error) { setError(error instanceof ApiError ? error.status === 409 ? "A escala foi alterada. Abra novamente o comunicado a partir da versão atual. Seus textos foram preservados." : error.status === 422 ? "Revise os campos. Publicação exige uma revisão publicada." : error.message : "Não foi possível preparar o comunicado. Tente novamente."); }
    finally { lock.current = false; setBusy(false); }
  }
  async function copy(value: string) {
    try { await navigator.clipboard.writeText(value); setFeedback("Texto copiado."); }
    catch { setFeedback("Não foi possível copiar automaticamente. Selecione o texto no campo e copie manualmente."); }
  }
  const safeSubject = !/[\r\n\0]/.test(subject);
  const mailto = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  const mailAllowed = generated && safeSubject && mailto.length <= 2000;
  return <div className="max-w-3xl space-y-6"><div><h1 className="text-3xl font-semibold">Comunicados</h1><p className="mt-2 text-muted-foreground">Prepare e revise o texto antes de compartilhar. O envio é feito por você no aplicativo de e-mail.</p></div>
    {scheduleId && <p className="rounded-xl border border-border p-4">Referência: {sourceKind === "revision" ? `revisão publicada ${sourceNumber}` : `RASCUNHO · versão ${sourceNumber} · não publicado`}. O texto usa a fotografia dessa origem.</p>}
    <form onSubmit={prepare} aria-busy={busy} className="space-y-4 rounded-2xl border border-border bg-card p-5"><Field id="communication-type" label="Tipo de comunicado"><select id="communication-type" className={controlClass} value={type} disabled={busy} onChange={event => setType(event.target.value as keyof typeof labels)}>{Object.entries(labels).map(([value, label]) => <option key={value} value={value} disabled={value === "publication" && sourceKind !== "revision"}>{label}</option>)}</select></Field><Field id="communication-message" label="Informações para o comunicado" hint="Até 2000 caracteres. Confira os detalhes antes de compartilhar."><textarea id="communication-message" name="message" maxLength={2000} rows={4} className={controlClass} disabled={busy} /></Field>{error && <Alert>{error}</Alert>}<Button type="submit" disabled={busy}>{busy ? "Preparando…" : generated ? "Preparar novamente" : "Preparar comunicado"}</Button>{generated && <p className="text-sm text-muted-foreground">Preparar novamente substitui o assunto e o corpo abaixo.</p>}</form>
    {!generated ? <p className="rounded-xl border border-dashed border-border p-5">Escolha o tipo e prepare um texto para começar.</p> : <section aria-label="Texto para revisão" className="space-y-4 rounded-2xl border border-border bg-card p-5"><Field id="communication-subject" label="Assunto"><Input id="communication-subject" maxLength={160} value={subject} onChange={event => setSubject(event.target.value)} /></Field><button className={secondaryClass} type="button" onClick={() => copy(subject)}>Copiar assunto</button><Field id="communication-body" label="Corpo do comunicado"><textarea id="communication-body" className={controlClass} rows={12} value={body} onChange={event => setBody(event.target.value)} /></Field><div className="flex flex-wrap gap-3"><button className={secondaryClass} type="button" onClick={() => copy(body)}>Copiar corpo</button>{mailAllowed && <a className={secondaryClass} href={mailto}>Abrir rascunho de e-mail</a>}</div>{!safeSubject && <Alert>Use um assunto de uma única linha.</Alert>}{!mailAllowed && safeSubject && <p role="status">O texto ultrapassa o limite conservador para abrir por e-mail. Copie o assunto e o corpo completos para o seu cliente; nenhum conteúdo foi cortado.</p>}<p className="text-sm text-muted-foreground">A abertura depende do cliente de e-mail configurado. Destinatários e anexos são adicionados por você. Se não abrir, copie os campos manualmente.</p></section>}
    <CommunicationAssistant text={body} onAccept={value => { setSubject(value.subject); setBody(value.body); setGenerated(true); }} />
    {feedback && <p role="status" className="rounded-xl bg-muted p-4">{feedback}</p>}
  </div>;
}

function CommunicationAssistant({ text, onAccept }: { text: string; onAccept: (value: { subject: string; body: string }) => void }) {
  const [status, setStatus] = useState<AssistantStatus | null>(null); const [error, setError] = useState(""); const [reload, setReload] = useState(0);
  const [input, setInput] = useState(""); const [consent, setConsent] = useState(false); const [busy, setBusy] = useState(false); const lock = useRef(false);
  const [suggestion, setSuggestion] = useState<{ subject: string; body: string } | null>(null);
  useEffect(() => { const controller = new AbortController(); api<AssistantStatus>("/assistant/status", { signal: controller.signal }).then(value => { if (!controller.signal.aborted) { setStatus(value); setError(""); } }).catch(() => { if (!controller.signal.aborted) setError("Assistência opcional indisponível. Prepare o texto manualmente."); }); return () => controller.abort(); }, [reload]);
  async function assist(intent: "draft" | "revise") {
    if (lock.current) return; lock.current = true; setBusy(true); setError(""); setSuggestion(null);
    try { const result = await api<{ subject: string; body: string }>("/assistant/communications", { method: "POST", body: JSON.stringify({ text: intent === "revise" ? text : input, intent, consent_external: consent }) }); setSuggestion(result); }
    catch (error) { setError(error instanceof ApiError ? error.message : "Não foi possível obter a sugestão. Seu texto original foi preservado."); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section aria-label="Assistência de redação" className="space-y-4 rounded-2xl border border-border bg-card p-5"><h2 className="text-xl font-semibold">Assistência de redação opcional</h2>{!status && !error && <p role="status">Consultando disponibilidade…</p>}{status && !status.enabled && <p>Assistência desativada. A preparação manual continua disponível.</p>}{error && <Alert>{error} {!status && <button className="underline" onClick={() => setReload(value => value + 1)}>Consultar novamente</button>}</Alert>}{status?.enabled && <><Field id="assistant-text" label="Orientações para o texto"><textarea id="assistant-text" className={controlClass} rows={3} maxLength={2000} value={input} disabled={busy} onChange={event => { setInput(event.target.value); setSuggestion(null); }} /></Field>{status.external_data && <label className="flex gap-3 text-sm"><input type="checkbox" checked={consent} disabled={busy} onChange={event => { setConsent(event.target.checked); setSuggestion(null); }} />Autorizo enviar o texto informado ao provedor externo.</label>}<div className="flex flex-wrap gap-3"><Button disabled={busy || !input.trim() || (status.external_data && !consent)} onClick={() => assist("draft")}>Sugerir texto</Button><Button disabled={busy || !text.trim() || text.length > 2000 || (status.external_data && !consent)} onClick={() => assist("revise")}>Revisar corpo atual</Button></div>{suggestion && <article className="space-y-3 rounded-xl border border-border p-4"><h3 className="font-semibold">Sugestão para revisão</h3><p className="break-words">{suggestion.subject}</p><p className="whitespace-pre-wrap break-words">{suggestion.body}</p><Button onClick={() => { onAccept(suggestion); setSuggestion(null); }}>Usar sugestão no editor</Button><p className="text-sm">A aceitação substitui o assunto e o corpo; revise antes de compartilhar.</p></article>}</>}</section>;
}
