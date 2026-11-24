import { PrivateShell } from "@/features/dashboard/private-shell";
import { ApiStatus } from "@/features/system-status/api-status";
import { requireSession } from "@/lib/auth/session";
import { DashboardSummary } from "@/features/dashboard/summary";
import Link from "next/link";
export default async function Dashboard() {
  const session = await requireSession();
  return <PrivateShell session={session} serverNow={session.server_now}>
    <header className="border-b border-border pb-7"><p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Seu espaço de trabalho</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">Dashboard</h1><p className="mt-3 text-sm text-muted-foreground">Conectada como {session.user.username}</p></header>
    <DashboardSummary />
    <section className="mt-6 rounded-[18px] border border-border bg-card p-6 sm:p-8"><h2 className="text-xl font-semibold">Organize sua base operacional</h2><p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">Cadastre unidades, vincule sua equipe e configure os horários habituais de cada colaboradora. Os indicadores refletem os cadastros atuais.</p><div className="mt-6 flex flex-wrap gap-3"><Link className="rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary" href="/units/new">Cadastrar unidade</Link><Link className="rounded-xl border border-border px-4 py-3 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary" href="/employees/new">Cadastrar colaboradora</Link></div></section>
    <section aria-label="Conexão do sistema" className="mt-6 rounded-2xl border border-border bg-white p-6"><ApiStatus /></section>
  </PrivateShell>;
}
