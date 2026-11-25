import { NextRequest, NextResponse } from "next/server";
import { authConfig } from "@/lib/auth/config";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const routes = new Map([
  ["auth/login", { method: "POST", upstream: "/api/v1/auth/login" }],
  ["auth/session", { method: "GET", upstream: "/api/v1/auth/session" }],
  ["auth/logout", { method: "POST", upstream: "/api/v1/auth/logout" }],
  ["health/ready", { method: "GET", upstream: "/api/v1/health/ready" }],
]);
type Context = { params: Promise<{ path: string[] }> };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
type OperationRoute = { methods: string[]; upstream: string; query: "units" | "employees" | "team" | "schedules" | "absences" | null };
function scheduleRoute(path: string[]): OperationRoute | null {
  if (path[0] !== "schedules") return null;
  const upstream = `/api/v1/${path.join("/")}`;
  if (path.length === 1) return { methods: ["GET", "POST"], upstream, query: "schedules" };
  if (!uuid.test(path[1] ?? "")) return null;
  if (path.length === 2) return { methods: ["GET"], upstream, query: null };
  if (path.length === 4 && path[2] === "coverage" && ["preview", "confirm"].includes(path[3])) return { methods: ["POST"], upstream, query: null };
  if (path.length === 3 && ["assignments", "validate", "publish"].includes(path[2])) return { methods: ["POST"], upstream, query: null };
  if (path.length === 3 && path[2] === "revisions") return { methods: ["GET"], upstream, query: null };
  if (path.length === 4 && ["assignments", "days"].includes(path[2]) && uuid.test(path[3])) return { methods: ["PATCH"], upstream, query: null };
  if (path.length === 4 && path[2] === "revisions" && /^[1-9]\d{0,8}$/.test(path[3])) return { methods: ["GET"], upstream, query: null };
  if (path.length === 5 && path[2] === "assignments" && uuid.test(path[3]) && path[4] === "remove") return { methods: ["POST"], upstream, query: null };
  return null;
}
function operationRoute(path: string[]): OperationRoute | null {
  if (path[0] === "schedules") return scheduleRoute(path);
  const [resource, id, child] = path;
  if (resource === "absences") {
    const upstream = `/api/v1/${path.join("/")}`;
    if (path.length === 1) return { methods: ["GET", "POST"], upstream, query: "absences" };
    if (!uuid.test(id ?? "")) return null;
    if (path.length === 2) return { methods: ["GET", "PATCH"], upstream, query: null };
    if (path.length === 3 && child === "cancel") return { methods: ["POST"], upstream, query: null };
    if (path.length === 3 && child === "events") return { methods: ["GET"], upstream, query: null };
    return null;
  }
  if (path.length === 2 && resource === "dashboard" && id === "operational-alerts") return { methods: ["GET"], upstream: "/api/v1/dashboard/operational-alerts", query: "schedules" };
  if (path.length === 2 && resource === "dashboard" && id === "summary") return { methods: ["GET"], upstream: "/api/v1/dashboard/summary", query: null };
  if (resource !== "units" && resource !== "employees") return null;
  if (path.length === 1) return { methods: ["GET", "POST"], upstream: `/api/v1/${resource}`, query: resource };
  if (!uuid.test(id ?? "")) return null;
  if (path.length === 2) return { methods: ["GET", "PATCH"], upstream: `/api/v1/${resource}/${id}`, query: null };
  if (path.length === 3 && resource === "units" && child === "employees") return { methods: ["GET"], upstream: `/api/v1/units/${id}/employees`, query: "team" };
  if (path.length === 3 && resource === "employees" && child === "work-patterns") return { methods: ["GET", "PUT"], upstream: `/api/v1/employees/${id}/work-patterns`, query: null };
  return null;
}
function validQuery(params: URLSearchParams, kind: OperationRoute["query"]) {
  const seen = new Set<string>();
  for (const [key, value] of params) {
    if (seen.has(key) || !kind) return false;
    seen.add(key);
    if (kind === "absences") {
      if (key === "employee_id") { if (!uuid.test(value)) return false; continue; }
      if (key === "type") { if (!["vacation", "day_off", "compensation", "other"].includes(value)) return false; continue; }
      if (key === "status") { if (!["active", "cancelled", "all"].includes(value)) return false; continue; }
      if (!["page", "page_size", "from_date", "to_date"].includes(key)) return false;
    }
    if ((kind === "schedules" || kind === "absences") && ["from_date", "to_date"].includes(key)) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0, 10) !== value) return false;
      continue;
    }
    if (kind === "schedules" && !["page", "page_size"].includes(key)) return false;
    if (key === "q") { if (value.length > (kind === "units" ? 120 : 140)) return false; }
    else if (key === "status") { if (!["active", "inactive", "all"].includes(value)) return false; }
    else if (key === "page" || key === "page_size") { if (!/^[1-9]\d*$/.test(value) || !Number.isSafeInteger(Number(value)) || (key === "page_size" && Number(value) > 100)) return false; }
    else if (kind === "employees" && key === "home_unit_id") { if (!uuid.test(value)) return false; }
    else if (kind === "employees" && key === "without_home_unit") { if (!["true", "false"].includes(value)) return false; }
    else return false;
  }
  return !(seen.has("home_unit_id") && seen.has("without_home_unit")) && !((kind === "schedules" || kind === "absences") && params.has("from_date") && params.has("to_date") && params.get("from_date")! > params.get("to_date")!);
}
function error(detail: string, status: number, allow?: string) {
  return NextResponse.json({ detail }, { status, headers: { "Cache-Control": "private, no-store", ...(allow ? { Allow: allow } : {}) } });
}
async function proxy(request: NextRequest, context: Context) {
  const { path } = await context.params;
  const authRoute = routes.get(path.join("/"));
  const route: OperationRoute | null = authRoute ? { methods: [authRoute.method], upstream: authRoute.upstream, query: null } : operationRoute(path);
  if (!route) return error("Não encontrado", 404);
  if (!route.methods.includes(request.method)) return error("Método não permitido", 405, route.methods.join(", "));
  if (!authRoute && !validQuery(request.nextUrl.searchParams, request.method === "GET" ? route.query : null)) return error("Filtros inválidos", 422);
  const config = authConfig();
  const headers = new Headers({ Accept: "application/json" });
  let body: ArrayBuffer | undefined;
  if (["POST", "PATCH", "PUT"].includes(request.method)) {
    if (request.headers.get("origin") !== config.origin || request.headers.get("x-recephub-csrf") !== "1") return error("Origem ou proteção CSRF inválida", 403);
    if (request.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !== "application/json") return error("Envie application/json", 415);
    const reader = request.body?.getReader();
    const chunks: Uint8Array[] = [];
    let total = 0;
    try {
      if (reader) while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        total += value.byteLength;
        if (total > 4096) { await reader.cancel(); return error("Corpo excede 4 KiB", 413); }
        chunks.push(value);
      }
    } catch { return error("Requisição inválida", 400); }
    finally { reader?.releaseLock(); }
    body = new ArrayBuffer(total);
    const bytes = new Uint8Array(body);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    headers.set("Origin", request.headers.get("origin")!);
    headers.set("X-RecepHub-CSRF", request.headers.get("x-recephub-csrf")!);
    headers.set("Content-Type", "application/json");
  }
  const cookie = request.cookies.get(config.cookieName);
  if (cookie && /^[A-Za-z0-9_-]{43}$/.test(cookie.value)) headers.set("Cookie", `${config.cookieName}=${cookie.value}`);
  try {
    const target = new URL(route.upstream, config.backend);
    if (!authRoute) target.search = request.nextUrl.search;
    if (!["http:", "https:"].includes(target.protocol) || target.username || target.password) return error("Serviço indisponível", 503);
    const upstream = await fetch(target, { method: request.method, headers, body, cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(5000) });
    if (upstream.status >= 300 && upstream.status < 400) return error("Serviço indisponível", 502);
    const responseHeaders = new Headers({ "Cache-Control": "private, no-store" });
    responseHeaders.set("Content-Type", upstream.headers.get("content-type") ?? "application/json");
    const date = upstream.headers.get("date");
    if (date) responseHeaders.set("Date", date);
    const retry = upstream.headers.get("retry-after");
    if (retry && /^\d+$/.test(retry)) responseHeaders.set("Retry-After", retry);
    for (const value of upstream.headers.getSetCookie()) if (value.startsWith(`${config.cookieName}=`)) responseHeaders.append("Set-Cookie", value);
    return new Response(upstream.status === 204 ? null : await upstream.arrayBuffer(), { status: upstream.status, headers: responseHeaders });
  } catch { return error("Serviço temporariamente indisponível", 503); }
}
export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
export const HEAD = proxy;
