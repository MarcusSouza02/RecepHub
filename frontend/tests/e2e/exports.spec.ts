import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
const headers = { Origin: "http://127.0.0.1:3180", "X-RecepHub-CSRF": "1" };
test.beforeEach(() => { execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint06-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" }); });
async function prepare(page: Page, multipage = false) {
  await page.goto("/login"); await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo"); await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!"); await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page).toHaveURL("/dashboard");
  const unit = await (await page.request.post("/api/v1/units", { headers, data: { name: "São João & <Norte> fictício" } })).json();
  const employee = await (await page.request.post("/api/v1/employees", { headers, data: { display_name: "Érica fictícia exportação", home_unit_id: unit.id } })).json();
  const days = Array.from({ length: 7 }, (_, weekday) => ({ weekday, state: weekday === 0 ? "working" : "non_working", start_time: weekday === 0 ? "08:00" : null, end_time: weekday === 0 ? "17:00" : null, break_start_time: weekday === 0 ? "12:00" : null, break_end_time: weekday === 0 ? "13:00" : null }));
  expect((await page.request.put(`/api/v1/employees/${employee.id}/work-patterns`, { headers, data: { days } })).status()).toBe(200);
  if (multipage) {
    const another = await (await page.request.post("/api/v1/employees", { headers, data: { display_name: "João fictício exportação", home_unit_id: unit.id } })).json();
    expect((await page.request.put(`/api/v1/employees/${another.id}/work-patterns`, { headers, data: { days } })).status()).toBe(200);
  }
  const response = await page.request.post("/api/v1/schedules", { headers, data: { week_start: "2026-11-30" } }); expect(response.status()).toBe(201); return await response.json();
}
test("published multipage PDF and PNG download through authenticated proxy", async ({ page }) => {
  const schedule = await prepare(page, true);
  expect((await page.request.post(`/api/v1/schedules/${schedule.id}/publish`, { headers, data: { expected_version: 1, confirmed: true } })).status()).toBe(201);
  await page.goto(`/schedules/${schedule.id}`);
  await page.getByRole("button", { name: "Conferir exportação", exact: true }).click();
  await expect(page.getByText(/2 página\(s\)/)).toBeVisible();
  const pdfWait = page.waitForEvent("download"); await page.getByRole("button", { name: "Baixar PDF", exact: true }).click(); const pdf = await pdfWait;
  expect(pdf.suggestedFilename()).toMatch(/\.pdf$/); const pdfPath = await pdf.path(); expect(pdfPath).not.toBeNull(); expect((await readFile(pdfPath!)).subarray(0, 5).toString()).toBe("%PDF-");
  await page.getByLabel("Formato", { exact: true }).selectOption("png"); await page.getByRole("button", { name: "Conferir exportação", exact: true }).click(); await page.getByLabel("Página do PNG").fill("2");
  const pngWait = page.waitForEvent("download"); await page.getByRole("button", { name: "Baixar PNG", exact: true }).click(); const png = await pngWait; const pngPath = await png.path(); expect(pngPath).not.toBeNull(); expect((await readFile(pngPath!)).subarray(0, 8)).toEqual(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
  expect((await page.request.get(`/api/v1/schedules/${schedule.id}/revisions`)).status()).toBe(200);
});
test("draft export requires explicit source and proxy rejects unsafe downloads", async ({ page }) => {
  const schedule = await prepare(page); await page.goto(`/schedules/${schedule.id}`);
  await expect(page.getByLabel("Versão para exportação")).toHaveValue("");
  await page.getByLabel("Versão para exportação").selectOption("draft");
  await expect(page.getByText("Todas as páginas serão marcadas como RASCUNHO NÃO PUBLICADO.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Conferir exportação", exact: true }).click(); await expect(page.getByText(/rascunho-v1/)).toBeVisible();
  const path = `/api/v1/schedules/${schedule.id}/exports`;
  expect((await page.request.get(path)).status()).toBe(405);
  expect((await page.request.post(path, { data: { source: { kind: "draft", expected_version: 1 } } })).status()).toBe(403);
  expect((await page.request.post(path, { headers, data: { source: { kind: "draft", expected_version: 999 } } })).status()).toBe(409);
  expect((await page.request.post(path + "/arbitrary", { headers, data: {} })).status()).toBe(404);
});
