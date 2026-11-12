import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authConfig } from "./config";
export type AuthSession = { user: { id: string; username: string }; expires_at: string; idle_expires_at: string; server_now: number };
export async function getSession(): Promise<AuthSession | null> {
  const config = authConfig();
  const cookie = (await cookies()).get(config.cookieName);
  if (!cookie || !/^[A-Za-z0-9_-]{43}$/.test(cookie.value)) return null;
  let response: Response;
  try { response = await fetch(new URL("/api/v1/auth/session", config.backend), {
    headers: { Cookie: `${config.cookieName}=${cookie.value}`, Accept: "application/json" },
    cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(5000) });
  } catch { throw new Error("Não foi possível verificar a sessão."); }
  if (response.status === 401) return null;
  if (response.status !== 200) throw new Error("Serviço temporariamente indisponível.");
  const data = await response.json() as AuthSession;
  if (!data?.user || typeof data.user.id !== "string" || typeof data.user.username !== "string" ||
      !Number.isFinite(Date.parse(data.expires_at)) || !Number.isFinite(Date.parse(data.idle_expires_at))) throw new Error("Resposta de sessão inválida.");
  const serverNow = Date.parse(response.headers.get("date") ?? "");
  if (!Number.isFinite(serverNow)) throw new Error("Horário de sessão inválido.");
  return { ...data, server_now: serverNow };
}
export async function requireSession() {
  const session = await getSession();
  if (!session) redirect("/login");
  return session;
}
