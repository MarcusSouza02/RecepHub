import { PrivateShell } from "@/features/dashboard/private-shell";
import { ApiStatus } from "@/features/system-status/api-status";
import { requireSession } from "@/lib/auth/session";
export default async function Dashboard() {
  const session = await requireSession();
  return <PrivateShell session={session} serverNow={session.server_now}>
    <header className="border-b border-border pb-7"><p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Seu espaço de trabalho</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">Dashboard</h1><p className="mt-3 text-sm text-muted-foreground">Conectada como {session.user.username}</p></header>
    <section className="mt-8 rounded-3xl border border-border bg-white p-8 sm:p-12"><div aria-hidden="true" className="mb-7 grid size-14 place-items-center rounded-2xl bg-muted text-2xl text-primary">↗</div><p className="text-xs font-semibold uppercase tracking-widest text-primary">Próximos passos</p><h2 className="mt-3 text-2xl font-semibold tracking-tight">Tudo começa com uma boa base.</h2><p className="mt-4 max-w-lg text-sm leading-7 text-muted-foreground">Seu acesso está configurado. Os recursos de equipes, unidades e escalas serão disponibilizados nas próximas sprints.</p><p className="mt-4 max-w-lg text-sm leading-7 text-muted-foreground">Ainda não há dados de gestão para exibir.</p></section>
    <section aria-label="Conexão do sistema" className="mt-6 rounded-2xl border border-border bg-white p-6"><ApiStatus /></section>
  </PrivateShell>;
}
