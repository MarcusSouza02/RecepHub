import Link from "next/link";
import type { ReactNode } from "react";
import { LogoutButton } from "@/features/auth/logout-button";
import { SessionMonitor } from "@/features/auth/session-monitor";
import type { AuthSession } from "@/lib/auth/session";
export function PrivateShell({ session, children, serverNow }: { session: AuthSession; children: ReactNode; serverNow: number }) {
  return <div className="min-h-dvh">
    <SessionMonitor expiresAt={session.expires_at} idleExpiresAt={session.idle_expires_at} serverNow={serverNow} />
    <a href="#conteudo" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-white focus:p-4">Pular para o conteúdo</a>
    <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-border bg-white p-6 md:flex">
      <Link href="/dashboard" className="text-2xl font-bold tracking-tight text-primary">RecepHub<span className="text-emerald-400">.</span></Link>
      <p className="mt-2 text-xs text-muted-foreground">Organização para cada dia</p>
      <nav aria-label="Navegação principal" className="mt-12"><Link href="/dashboard" aria-current="page" className="block rounded-xl bg-muted px-4 py-3 text-sm font-semibold text-primary focus-visible:outline-2 focus-visible:outline-primary">Dashboard</Link></nav>
      <div className="mt-auto border-t border-border pt-5"><p className="text-xs text-muted-foreground">Sua conta</p><p className="my-3 break-words text-sm font-semibold">{session.user.username}</p><LogoutButton /></div>
    </aside>
    <header className="border-b border-border bg-white p-4 md:hidden"><div className="flex items-center justify-between gap-4"><Link href="/dashboard" className="text-xl font-bold text-primary">RecepHub.</Link><LogoutButton /></div><nav aria-label="Navegação principal" className="mt-5"><Link href="/dashboard" aria-current="page" className="rounded-xl bg-muted px-4 py-2 text-sm font-semibold text-primary">Dashboard</Link></nav><p className="mt-4 break-words text-xs text-muted-foreground">{session.user.username}</p></header>
    <main id="conteudo" tabIndex={-1} className="p-5 md:ml-64 md:p-10"><div className="mx-auto max-w-6xl">{children}</div></main>
  </div>;
}
