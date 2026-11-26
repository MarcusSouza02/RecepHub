import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";
const headers = { Origin: "http://127.0.0.1:3180", "X-RecepHub-CSRF": "1" };
test.beforeEach(() => { execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint06-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" }); });
async function openSchedule(page: Page) {
  await page.goto("/login"); await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo"); await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!"); await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page).toHaveURL("/dashboard");
  const response = await page.request.post("/api/v1/schedules", { headers, data: { week_start: "2026-11-30" } }); expect(response.status()).toBe(201); const schedule = await response.json(); await page.goto(`/schedules/${schedule.id}`); return schedule;
}
test("assistant is optional and disabled by default", async ({ page }) => {
  await openSchedule(page);
  await expect(page.getByText("A assistência está desativada. A edição manual, os comunicados e as exportações continuam disponíveis.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Gerar prévia", exact: true })).toHaveCount(0);
});
test("mocked structured proposal requires confirmation and invalidates changed input", async ({ page }) => {
  await page.route("**/api/v1/assistant/status", route => route.fulfill({ json: { enabled: true, provider: "fictional-ui-mock", external_data: false, proposals_enabled: true } }));
  const schedule = await openSchedule(page); let confirms = 0;
  const before = { id: "fictional-assignment", unit_id: "11111111-1111-4111-8111-111111111111", unit_name: "Unidade fictícia", start_time: "08:00:00", end_time: "17:00:00", break_start_time: null, break_end_time: null, position: null };
  const after = { ...before, break_start_time: "12:00:00", break_end_time: "13:00:00", position: "Recepção revisada" };
  await page.route("**/api/v1/schedules/*/proposals/preview", route => route.fulfill({ json: { status: "ready", message: "Prévia fictícia para validar a interface", differences: [{ day_id: "fictional-day", before: [before], after: [after] }], impediments: [], receipt: "fictional-ui-receipt", expires_in: 600 } }));
  await page.route("**/api/v1/schedules/*/proposals/confirm", route => { confirms++; return route.fulfill({ json: { ...schedule, version: schedule.version + 1 } }); });
  await page.getByLabel("Pedido para a escala", { exact: true }).fill("Pedido fictício para revisão");
  await page.getByRole("button", { name: "Gerar prévia", exact: true }).click();
  await expect(page.getByText("Prévia fictícia para validar a interface")).toBeVisible(); expect(confirms).toBe(0);
  await expect(page.getByText("Antes: Unidade: Unidade fictícia (11111111) · Entrada: 08:00 · Saída: 17:00 · Sem intervalo · Atividade: Sem atividade", { exact: true })).toBeVisible();
  await expect(page.getByText("Depois: Unidade: Unidade fictícia (11111111) · Entrada: 08:00 · Saída: 17:00 · Intervalo: 12:00–13:00 · Atividade: Recepção revisada", { exact: true })).toBeVisible();
  expect(confirms).toBe(0);
  await page.getByLabel("Pedido para a escala", { exact: true }).fill("Outro pedido fictício");
  await expect(page.getByRole("button", { name: "Revisar e confirmar proposta", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Gerar prévia", exact: true }).click();
  await page.getByRole("button", { name: "Revisar e confirmar proposta", exact: true }).click();
  expect(confirms).toBe(0);
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect.poll(() => confirms).toBe(1);
  await expect(page.getByRole("button", { name: "Revisar e confirmar proposta", exact: true })).toHaveCount(0);
});

test("mocked homonymous unit change displays distinct identifiers and copyable references", async ({ page }) => {
  await page.route("**/api/v1/assistant/status", route => route.fulfill({ json: { enabled: true, provider: "fictional-ui-mock", external_data: false, proposals_enabled: true } }));
  const initial = await openSchedule(page);
  const employee = await (await page.request.post("/api/v1/employees", { headers, data: { display_name: "Pessoa homônima fictícia" } })).json();
  const first = await (await page.request.post("/api/v1/units", { headers, data: { name: "Unidade homônima" } })).json();
  const second = await (await page.request.post("/api/v1/units", { headers, data: { name: "Unidade homônima" } })).json();
  const schedule = await (await page.request.post("/api/v1/schedules", { headers, data: { week_start: "2026-12-07" } })).json();
  const day = schedule.days[0];
  const added = await (await page.request.post(`/api/v1/schedules/${schedule.id}/assignments`, { headers, data: { expected_version: schedule.version, day_id: day.id, unit_id: first.id, start_time: "08:00", end_time: "10:00" } })).json();
  const before = added.days.find((row: { id: string }) => row.id === day.id).assignments;
  const after = before.map((row: object) => ({ ...row, unit_id: second.id, unit_name: second.name }));
  await page.route("**/api/v1/schedules/*/proposals/preview", route => route.fulfill({ json: { status: "ready", message: "Troca fictícia entre homônimas", differences: [{ day_id: day.id, before, after }], impediments: [], receipt: "fictional-homonym-receipt", expires_in: 600 } }));
  await page.goto(`/schedules/${schedule.id}`);
  await page.getByText("Referências desta escala", { exact: true }).click();
  await expect(page.getByText(`Pessoa: ${employee.id}`, { exact: true }).first()).toBeVisible();
  await expect(page.getByText(`Dia: ${day.id}`, { exact: true }).first()).toBeVisible();
  await expect(page.getByText(`Unidade Unidade homônima: ${first.id}`, { exact: true })).toBeVisible();
  await page.getByLabel("Pedido para a escala", { exact: true }).fill(`Trocar unidade por ${second.id}`);
  await page.getByRole("button", { name: "Gerar prévia", exact: true }).click();
  await expect(page.getByText(new RegExp(`Antes: Unidade: Unidade homônima \\(${first.id.slice(0, 8)}\\)`))).toBeVisible();
  await expect(page.getByText(new RegExp(`Depois: Unidade: Unidade homônima \\(${second.id.slice(0, 8)}\\)`))).toBeVisible();
  expect(initial.id).not.toBe(schedule.id);
});
