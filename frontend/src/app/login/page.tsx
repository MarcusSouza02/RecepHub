import { redirect } from "next/navigation";
import { LoginForm } from "@/features/auth/login-form";
import { getSession } from "@/lib/auth/session";
export default async function LoginPage() {
  if (await getSession()) redirect("/dashboard");
  return <main className="flex min-h-dvh items-center justify-center px-5 py-12"><section className="w-full max-w-md rounded-3xl border border-border bg-white p-7 shadow-sm sm:p-10" aria-labelledby="login-title">
    <p className="text-lg font-bold tracking-tight text-primary">RecepHub<span className="text-emerald-400">.</span></p>
    <p className="mt-8 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Seu espaço de organização</p>
    <h1 id="login-title" className="mt-3 text-3xl font-semibold tracking-tight">Acesse sua conta</h1>
    <p className="mt-3 text-sm leading-6 text-muted-foreground">Mais clareza para a rotina das recepções laboratoriais.</p>
    <LoginForm /><p className="mt-8 border-t border-border pt-5 text-xs leading-5 text-muted-foreground">Acesso pessoal. Para alterar sua senha, utilize a administração local da conta.</p>
  </section></main>;
}
