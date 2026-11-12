export async function checkApi(signal: AbortSignal): Promise<void> {
  const response = await fetch("/api/v1/health/ready", {
    signal,
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("API indisponível");
  const data: unknown = await response.json();
  if (
    typeof data !== "object" || data === null ||
    !("status" in data) || data.status !== "ok" ||
    !("database" in data) || data.database !== "ok"
  ) throw new Error("Resposta de saúde inválida");
}
