const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function checkApi(signal: AbortSignal): Promise<void> {
  const response = await fetch(`${API_URL.replace(/\/$/, "")}/api/v1/health/ready`, {
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
