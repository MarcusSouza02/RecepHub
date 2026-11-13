export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}
const fallback = (status: number) => status === 401 ? "Sua sessão expirou. Entre novamente." : status === 404 ? "Registro não encontrado." : status === 409 ? "A operação não pôde ser concluída. Revise os vínculos do cadastro." : status === 422 ? "Revise os dados informados." : "Serviço temporariamente indisponível. Tente novamente.";
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\") || path.includes("#")) throw new ApiError(400, "Caminho de operação inválido.");
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  const method = (options.method ?? "GET").toUpperCase();
  if (["POST", "PATCH", "PUT"].includes(method)) { headers.set("Content-Type", "application/json"); headers.set("X-RecepHub-CSRF", "1"); }
  const response = await fetch(`/api/v1${path}`, { ...options, method, headers, credentials: "same-origin", cache: "no-store", redirect: "error" });
  if (response.status === 401 && typeof window !== "undefined") window.location.replace("/login");
  if (!response.ok) {
    let detail: unknown;
    try { detail = (await response.json() as { detail?: unknown }).detail; } catch { /* Use the generic message for non-JSON responses. */ }
    const safeDetail = typeof detail === "string" && detail.length > 0 && detail.length <= 300 && !/[<>\r\n\u0000-\u001f]/.test(detail) && !/sql|traceback|exception|password|token|cookie|secret/i.test(detail);
    throw new ApiError(response.status, safeDetail ? detail as string : fallback(response.status));
  }
  if (response.status === 204) return undefined as T;
  return await response.json() as T;
}
