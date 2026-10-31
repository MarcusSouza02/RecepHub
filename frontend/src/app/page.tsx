import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiStatus } from "@/features/system-status/api-status";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-6 py-5">
          <span aria-hidden="true" className="grid size-10 place-items-center rounded-xl bg-primary text-lg font-bold text-primary-foreground">R</span>
          <span className="text-xl font-semibold tracking-tight">RecepHub</span>
          <span className="ml-auto rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">Em desenvolvimento</span>
        </div>
      </header>
      <main className="mx-auto grid w-full max-w-6xl flex-1 content-center gap-10 px-6 py-16 md:grid-cols-[1.2fr_1fr] md:gap-16 md:py-24">
        <section className="space-y-6">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">Um lugar para organizar a rotina</p>
          <h1 className="max-w-xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">Mais clareza para cada dia da recepção.</h1>
          <p className="max-w-lg text-lg leading-8 text-muted-foreground">O RecepHub está sendo preparado para reunir equipes, unidades e escalas em um só lugar.</p>
          <p className="text-sm leading-6 text-muted-foreground">Esta é a versão inicial do projeto. As funcionalidades de gestão serão disponibilizadas nas próximas etapas.</p>
        </section>
        <Card className="self-center">
          <CardHeader>
            <CardTitle>Conexão do sistema</CardTitle>
            <CardDescription>Acompanhe a disponibilidade do ambiente.</CardDescription>
          </CardHeader>
          <CardContent><ApiStatus /></CardContent>
        </Card>
      </main>
      <footer className="mx-auto w-full max-w-6xl px-6 py-6 text-xs text-muted-foreground">RecepHub · Fundação do projeto · Sprint 01</footer>
    </div>
  );
}
