import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";
const headers = { Origin: "http://127.0.0.1:3180", "X-RecepHub-CSRF": "1" };
test.beforeEach(() => { execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint04-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" }); });
async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo");
  await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL("/dashboard");
}
async function seed(page: Page, complete = true) {
  const unitResponse = await page.request.post("/api/v1/units", { headers, data: { name: "Unidade fictícia escala" } });
  expect(unitResponse.status()).toBe(201); const unit = await unitResponse.json();
  const employeeResponse = await page.request.post("/api/v1/employees", { headers, data: { display_name: "Pessoa fictícia escala", home_unit_id: unit.id } });
  expect(employeeResponse.status()).toBe(201); const employee = await employeeResponse.json();
  if (complete) {
    const days = Array.from({ length: 7 }, (_, weekday) => ({ weekday, state: weekday === 0 ? "working" : "non_working", start_time: weekday === 0 ? "08:00" : null, end_time: weekday === 0 ? "17:00" : null, break_start_time: weekday === 0 ? "12:00" : null, break_end_time: weekday === 0 ? "13:00" : null }));
    expect((await page.request.put(`/api/v1/employees/${employee.id}/work-patterns`, { headers, data: { days } })).status()).toBe(200);
  }
  return { unit, employee };
}
async function generate(page: Page) {
  await page.goto("/schedules");
  await page.getByLabel("Segunda-feira da semana").fill("2026-11-30");
  await page.getByRole("button", { name: "Gerar semana", exact: true }).click();
  await expect(page).toHaveURL(/\/schedules\/[0-9a-f-]+$/);
  await expect(page.getByRole("heading", { name: /Semana de/ })).toBeVisible();
  return page.url().split("/").at(-1)!;
}
test("weekly edit publication history and habitual remain independent", async ({ page }) => {
  await login(page); const { employee } = await seed(page); const id = await generate(page);
  await page.getByRole("button", { name: "Editar período", exact: true }).click();
  await page.getByLabel("Guichê ou atividade (opcional)").fill("Recepção A");
  await page.getByRole("button", { name: "Salvar período", exact: true }).click();
  await expect(page.getByText("Recepção A", { exact: true })).toBeVisible();
  const habitual = await (await page.request.get(`/api/v1/employees/${employee.id}/work-patterns`)).json();
  expect(habitual.days[0].start_time).toBe("08:00:00"); expect(habitual.days[0].end_time).toBe("17:00:00");
  await page.getByRole("button", { name: "Publicar revisão", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByText("Publicação · revisão 1 · somente leitura", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Editar período", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Editar conteúdo corrente", exact: true }).click();
  await page.getByRole("button", { name: "Editar período", exact: true }).click();
  await page.getByLabel("Guichê ou atividade (opcional)").fill("Recepção B");
  await page.getByRole("button", { name: "Salvar período", exact: true }).click();
  await expect(page.getByText("Recepção B", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Publicar revisão", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByText("Publicação · revisão 2 · somente leitura", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Revisão 1", exact: true }).click();
  await expect(page.getByText("Recepção A", { exact: true })).toBeVisible();
  await expect(page.getByText("Recepção B", { exact: true })).toHaveCount(0);
  const first = await (await page.request.get(`/api/v1/schedules/${id}/revisions/1`)).json();
  expect(first.snapshot.days.flatMap((d: { assignments: { position: string }[] }) => d.assignments)[0].position).toBe("Recepção A");
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", await page.locator("body").evaluate(el => el.clientWidth));
});
test("pending generation requires deliberate resolution and exclusion reason", async ({ page }) => {
  await login(page); await seed(page, false); await generate(page);
  await expect(page.getByText("Horário habitual pendente.")).toHaveCount(7);
  await page.getByRole("button", { name: "Resolver dia", exact: true }).first().click();
  await page.getByLabel("Estado explícito").selectOption("excluded");
  await expect(page.getByLabel("Motivo operacional")).toHaveAttribute("required", "");
  await page.getByLabel("Motivo operacional").fill("Retirada operacional fictícia");
  await page.getByRole("button", { name: "Salvar estado", exact: true }).click();
  await expect(page.getByText("Retirada operacional fictícia", { exact: true })).toBeVisible();
  await expect(page.getByText("Horário habitual pendente.")).toHaveCount(6);
});
test("stale form preserves typed changes until explicit reload", async ({ page }) => {
  await login(page); await seed(page); const id = await generate(page);
  await page.getByRole("button", { name: "Editar período", exact: true }).click();
  await page.getByLabel("Guichê ou atividade (opcional)").fill("Minha edição preservada");
  const current = await (await page.request.get(`/api/v1/schedules/${id}`)).json();
  const assignment = current.days.flatMap((day: { assignments: { id: string }[] }) => day.assignments)[0];
  expect((await page.request.patch(`/api/v1/schedules/${id}/assignments/${assignment.id}`, { headers, data: { expected_version: current.version, position: "Outro navegador" } })).status()).toBe(200);
  await page.getByRole("button", { name: "Salvar período", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Seu formulário foi preservado" })).toBeVisible();
  await expect(page.getByLabel("Guichê ou atividade (opcional)")).toHaveValue("Minha edição preservada");
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Recarregar escala", exact: true }).click();
  await expect(page.getByText("Outro navegador", { exact: true })).toBeVisible();
});
test("schedules require session and strict proxy write guards", async ({ page }) => {
  await page.goto("/schedules"); await expect(page).toHaveURL("/login");
  expect((await page.request.get("/api/v1/schedules")).status()).toBe(401);
  await login(page);
  expect((await page.request.post("/api/v1/schedules", { data: { week_start: "2026-11-30" } })).status()).toBe(403);
  expect((await page.request.post("/api/v1/schedules", { headers: { ...headers, Origin: "https://untrusted.invalid" }, data: { week_start: "2026-11-30" } })).status()).toBe(403);
  expect((await page.request.get("/api/v1/schedules?unexpected=true")).status()).toBe(422);
  expect((await page.request.delete("/api/v1/schedules")).status()).toBe(405);
  expect((await page.request.get("/api/v1/schedules/not-a-uuid")).status()).toBe(404);
});

test("unit filter hides other periods and history cannot retain an open editor", async ({ page }) => {
  await login(page); const { unit } = await seed(page); const id = await generate(page);
  const unitResponse = await page.request.post("/api/v1/units", { headers, data: { name: "Unidade fictícia secundária" } });
  expect(unitResponse.status()).toBe(201); const secondUnit = await unitResponse.json();
  const current = await (await page.request.get(`/api/v1/schedules/${id}`)).json();
  const monday = current.days.find((day: { work_date: string }) => day.work_date === "2026-11-30");
  expect((await page.request.post(`/api/v1/schedules/${id}/assignments`, { headers, data: { expected_version: current.version, day_id: monday.id, unit_id: secondUnit.id, start_time: "17:00", end_time: "18:00", position: "Período secundário" } })).status()).toBe(200);
  await page.getByRole("button", { name: "Recarregar escala", exact: true }).click();
  await expect(page.getByText("Período secundário", { exact: true })).toBeVisible();
  await page.getByLabel("Unidade", { exact: true }).selectOption(unit.id);
  await expect(page.getByText("Período secundário", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Editar período", exact: true })).toHaveCount(1);
  await page.getByLabel("Unidade", { exact: true }).selectOption("");
  await page.getByRole("button", { name: "Publicar revisão", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByText("Publicação · revisão 1 · somente leitura", { exact: true })).toBeVisible();
  await page.getByLabel("Unidade", { exact: true }).selectOption(unit.id);
  await expect(page.getByText("Período secundário", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Editar conteúdo corrente", exact: true }).click();
  await page.getByRole("button", { name: "Editar período", exact: true }).click();
  await expect(page.getByRole("button", { name: "Revisão 1", exact: true })).toBeDisabled();
  await expect(page.getByLabel("Guichê ou atividade (opcional)")).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.getByRole("button", { name: "Revisão 1", exact: true }).click();
  await expect(page.getByText("Publicação · revisão 1 · somente leitura", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Salvar período", exact: true })).toHaveCount(0);
});
