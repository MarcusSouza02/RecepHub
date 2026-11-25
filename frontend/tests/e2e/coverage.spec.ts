import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

const headers = { Origin: "http://127.0.0.1:3180", "X-RecepHub-CSRF": "1" };
test.beforeEach(() => {
  execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint05-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" });
});
async function prepare(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo");
  await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL("/dashboard");
  const unitResponse = await page.request.post("/api/v1/units", { headers, data: { name: "Destino fictício cobertura" } });
  expect(unitResponse.status()).toBe(201);
  const unit = await unitResponse.json();
  const employeeResponse = await page.request.post("/api/v1/employees", { headers, data: { display_name: "Candidata fictícia" } });
  expect(employeeResponse.status()).toBe(201);
  const employee = await employeeResponse.json();
  const days = Array.from({ length: 7 }, (_, weekday) => ({ weekday, state: weekday === 0 ? "working" : "non_working", start_time: weekday === 0 ? "08:00" : null, end_time: weekday === 0 ? "17:00" : null }));
  expect((await page.request.put(`/api/v1/employees/${employee.id}/work-patterns`, { headers, data: { days } })).status()).toBe(200);
  const scheduleResponse = await page.request.post("/api/v1/schedules", { headers, data: { week_start: "2026-11-30" } });
  expect(scheduleResponse.status()).toBe(201);
  const schedule = await scheduleResponse.json();
  await page.goto(`/schedules/${schedule.id}`);
  await page.getByLabel("Unidade da cobertura").selectOption(unit.id);
  await page.getByLabel("Início da cobertura").fill("09:00");
  await page.getByLabel("Fim da cobertura").fill("10:00");
  return { employee, unit, schedule };
}

test("coverage preview does not mutate and confirmation changes draft only", async ({ page }) => {
  const { schedule } = await prepare(page);
  await page.getByRole("button", { name: "Consultar candidatas", exact: true }).click();
  await expect(page.getByText("Disponível", { exact: true })).toBeVisible();
  const before = await (await page.request.get(`/api/v1/schedules/${schedule.id}`)).json();
  expect(before.version).toBe(1);
  await page.getByRole("button", { name: "Selecionar Candidata fictícia", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByText(/Cobertura adicionada ao rascunho/)).toBeVisible();
  const after = await (await page.request.get(`/api/v1/schedules/${schedule.id}`)).json();
  expect(after.version).toBe(2); expect(after.status).toBe("draft"); expect(after.latest_revision_number).toBe(0);
  expect(after.days.flatMap((day: { assignments: unknown[] }) => day.assignments)).toHaveLength(1);
});

test("absence created after preview blocks confirmation and preserves intent", async ({ page }) => {
  const { employee } = await prepare(page);
  await page.getByRole("button", { name: "Consultar candidatas", exact: true }).click();
  await page.getByRole("button", { name: "Selecionar Candidata fictícia", exact: true }).click();
  const absence = await page.request.post("/api/v1/absences", { headers, data: { employee_id: employee.id, type: "other", mode: "full_day", start_date: "2026-11-30", end_date: "2026-11-30" } });
  expect(absence.status()).toBe(201);
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Seu formulário foi preservado" })).toBeVisible();
  await expect(page.getByLabel("Início da cobertura")).toHaveValue("09:00");
  await page.getByRole("button", { name: "Consultar candidatas", exact: true }).click();
  await expect(page.getByText("Indisponível", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Selecionar Candidata fictícia", exact: true })).toHaveCount(0);
});
