import { ApiError } from "./operations";

export async function downloadExport(scheduleId: string, payload: object) {
  if (!/^[0-9a-f-]{36}$/i.test(scheduleId)) throw new Error("Escala inválida.");
  const response = await fetch(`/api/v1/schedules/${scheduleId}/exports`, {
    method: "POST", credentials: "same-origin", cache: "no-store", redirect: "error",
    headers: { "Content-Type": "application/json", "X-RecepHub-CSRF": "1" },
    body: JSON.stringify(payload), signal: AbortSignal.timeout(45000),
  });
  if (response.status === 401) window.location.replace("/login");
  if (!response.ok) throw new ApiError(response.status, response.status === 409 ? "A escala mudou. Consulte a exportação novamente." : "Não foi possível gerar o arquivo. Tente novamente.");
  const mime = response.headers.get("Content-Type")?.split(";")[0];
  if (!mime || !["application/pdf", "image/png"].includes(mime)) throw new Error("Formato de arquivo inesperado.");
  const blob = await response.blob();
  if (blob.size > 20 * 1024 * 1024) throw new Error("O arquivo excede o limite permitido.");
  const supplied = response.headers.get("Content-Disposition")?.match(/filename="([a-zA-Z0-9._-]+)"/)?.[1];
  const name = supplied ?? `recephub-escala.${mime === "application/pdf" ? "pdf" : "png"}`;
  const url = URL.createObjectURL(blob), link = document.createElement("a");
  link.href = url; link.download = name; document.body.append(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
