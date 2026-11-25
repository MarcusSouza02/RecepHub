import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";
const headers = { Origin: "http://127.0.0.1:3180", "X-RecepHub-CSRF": "1" };
test.beforeEach(() => { execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint05-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" }); });
async function seed(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo");
  await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL("/dashboard");
  const response = await page.request.post("/api/v1/employees", { headers, data: { display_name: "Pessoa fictícia ausência" } });
  expect(response.status()).toBe(201);
  return await response.json();
}
async function create(page: Page, employeeId: string, partial = false) {
  await page.goto("/absences/new");
  await page.getByLabel("Colaboradora *", { exact: true }).selectOption(employeeId);
  if (partial) await page.getByLabel("Período *", { exact: true }).selectOption("partial");
  await page.getByLabel(partial ? "Data *" : "Data inicial *", { exact: true }).fill("2026-11-24");
  if (partial) { await page.getByLabel("Horário inicial *", { exact: true }).fill("08:00"); await page.getByLabel("Horário final *", { exact: true }).fill("10:00"); }
  else await page.getByLabel("Data final *", { exact: true }).fill("2026-11-25");
  await page.getByLabel("Observações", { exact: true }).fill("Registro fictício");
  await page.getByRole("button", { name: "Salvar ausência", exact: true }).click();
  await expect(page).toHaveURL(/\/absences\/[0-9a-f-]+$/);
  await expect(page.getByRole("heading", { name: /Férias · Pessoa fictícia/ })).toBeVisible();
  return page.url().split("/").at(-1)!;
}
test("absence create edit overlap cancellation and history", async ({ page }) => {
  const employee = await seed(page); const id = await create(page, employee.id);
  await page.getByRole("link", { name: "Editar ausência", exact: true }).click();
  await page.getByLabel("Tipo *", { exact: true }).selectOption("day_off");
  await page.getByLabel("Observações", { exact: true }).fill("Observação atualizada");
  await page.getByRole("button", { name: "Salvar ausência", exact: true }).click();
  await expect(page.getByText("Versão 2 · Alterada", { exact: true })).toBeVisible();
  const second = await create(page, employee.id, true);
  await expect(page.getByText(/Esta ausência se sobrepõe/)).toBeVisible();
  await page.getByRole("button", { name: "Cancelar ausência", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByText("Versão 2 · Cancelada", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Editar ausência", exact: true })).toHaveCount(0);
  await page.goto(`/absences/${id}`);
  await expect(page.getByText(/Esta ausência se sobrepõe/)).toHaveCount(0);
  const events = await (await page.request.get(`/api/v1/absences/${second}/events`)).json();
  expect(events.items.map((event: { action: string }) => event.action)).toEqual(["created", "cancelled"]);
  await page.goto("/absences");
  await page.getByLabel("Status", { exact: true }).selectOption("cancelled");
  await expect(page.getByRole("link", { name: "Pessoa fictícia ausência · Férias", exact: true })).toBeVisible();
  await page.getByLabel("Tipo", { exact: true }).selectOption("compensation");
  await expect(page.getByText(/Nenhuma ausência encontrada/)).toBeVisible();
});
test("obsolete version preserves entered form", async ({ page }) => {
  const employee = await seed(page); const id = await create(page, employee.id);
  await page.getByRole("link", { name: "Editar ausência", exact: true }).click();
  await page.getByLabel("Observações", { exact: true }).fill("Preservar meu texto");
  const response = await page.request.patch(`/api/v1/absences/${id}`, { headers, data: { expected_version: 1, notes: "Outra edição fictícia" } });
  expect(response.status()).toBe(200);
  await page.getByRole("button", { name: "Salvar ausência", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Seus campos foram preservados" })).toContainText("Seus campos foram preservados");
  await expect(page.getByLabel("Observações", { exact: true })).toHaveValue("Preservar meu texto");
  await expect(page.getByRole("link", { name: "Consultar versão atual em outra aba" })).toBeVisible();
});
test("partial absence mobile layout and validation", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const employee = await seed(page); await create(page, employee.id, true);
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", await page.locator("body").evaluate(el => el.clientWidth));
  await page.getByRole("link", { name: "Editar ausência", exact: true }).click();
  await page.getByLabel("Horário final *", { exact: true }).fill("07:00");
  await page.getByRole("button", { name: "Salvar ausência", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "horário final posterior" })).toContainText("horário final posterior");
});

test("dashboard alerts reflect active absence and cancellation", async ({ page }) => {
  const employee = await seed(page); const id = await create(page, employee.id);
  await page.goto("/dashboard");
  await page.getByLabel("Alertas a partir de").fill("2026-11-24");
  await page.getByLabel("Alertas até").fill("2026-11-25");
  await page.getByRole("button", { name: "Consultar alertas", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Ausências ativas: 1", exact: true })).toBeVisible();
  const cancelled = await page.request.post(`/api/v1/absences/${id}/cancel`, { headers, data: { expected_version: 1, confirmed: true } });
  expect(cancelled.status()).toBe(200);
  await page.getByRole("button", { name: "Consultar alertas", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Ausências ativas: 0", exact: true })).toBeVisible();
});
