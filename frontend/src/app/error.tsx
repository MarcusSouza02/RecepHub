"use client";
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="flex min-h-dvh items-center justify-center p-6"><section className="max-w-md rounded-2xl border border-border bg-white p-8"><h1 className="text-2xl font-semibold">Não foi possível carregar</h1><p className="mt-4 text-muted-foreground">O serviço pode estar temporariamente indisponível.</p><button onClick={reset} className="mt-6 min-h-11 rounded-xl bg-primary px-5 py-3 text-white">Tentar novamente</button></section></main>;
}
