import Link from "next/link";
import type { ReactNode } from "react";
import { LogoutButton } from "@/features/auth/logout-button";
import { SessionMonitor } from "@/features/auth/session-monitor";
import type { AuthSession } from "@/lib/auth/session";
import { Navigation } from "./navigation";
export function PrivateShell({ session, children, serverNow }: { session: AuthSession; children: ReactNode; serverNow: number }) {
  return <div className="min-h-dvh">
    <SessionMonitor expiresAt={session.expires_at} idleExpiresAt={session.idle_expires_at} serverNow={serverNow} />
    <a href="#conteudo" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-white focus:p-4">Pular para o conteúdo</a>
    <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-[oklch(.25_.05_152)] p-6 text-white/80 md:flex">
      <Link href="/dashboard" className="text-2xl font-bold tracking-tight text-white">RecepHub<span className="text-emerald-400">.</span></Link>
      <p className="mb-12 mt-2 text-xs text-white/60">Organização para cada dia</p>
      <Navigation />
      <div className="mt-auto border-t border-white/15 pt-5 [&_button:hover]:text-foreground"><p className="text-xs text-white/60">Sua conta</p><p className="my-3 break-words text-sm font-semibold">{session.user.username}</p><LogoutButton /></div>
    </aside>
    <header className="border-b border-border bg-white px-6 py-4 md:ml-64"><div className="flex min-h-8 items-center justify-between gap-4"><Link href="/dashboard" className="text-xl font-bold text-primary md:hidden">RecepHub.</Link><p className="ml-auto text-sm text-muted-foreground">{session.user.username}</p><div className="md:hidden"><LogoutButton /></div></div><div className="mt-4 rounded-xl bg-[oklch(.25_.05_152)] p-2 text-white/80 md:hidden"><Navigation /></div></header>
    <main id="conteudo" tabIndex={-1} className="p-5 md:ml-64 md:p-6"><div className="mx-auto max-w-6xl">{children}</div></main>
  </div>;
}
