import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

const headers = { Origin: "http://127.0.0.1:3180", "X-RecepHub-CSRF": "1" };
test.beforeEach(() => {
  execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint02-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" });
});
async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo");
  await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL("/dashboard");
}
async function createUnit(page: Page) {
  await page.goto("/units/new");
  await page.getByLabel("Nome da unidade").fill("Unidade fictícia Aurora");
  await page.getByLabel("Cidade", { exact: true }).fill("Cidade de teste");
  await page.getByRole("button", { name: "Salvar unidade", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Unidade fictícia Aurora", exact: true })).toBeVisible();
  return page.url().split("/").at(-1)!;
}

test("units and employees preserve assignments through unit inactivation", async ({ page }) => {
  await login(page);
  const unitId = await createUnit(page);
  await page.goto("/employees/new");
  await page.getByLabel("Nome da colaboradora").fill("Pessoa fictícia Aurora");
  await page.getByLabel("Unidade habitual", { exact: true }).selectOption(unitId);
  await page.getByRole("button", { name: "Salvar colaboradora", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pessoa fictícia Aurora", exact: true })).toBeVisible();
  const employeeUrl = page.url();
  await page.goto(`/units/${unitId}`);
  await expect(page.getByRole("link", { name: "Pessoa fictícia Aurora", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Inativar", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Reativar", exact: true })).toBeVisible();
  await page.goto(employeeUrl);
  await expect(page.getByText("O vínculo foi preservado, mas a unidade habitual está inativa.")).toBeVisible();
  await page.getByRole("link", { name: "Editar colaboradora", exact: true }).click();
  await expect(page.getByLabel("Unidade habitual", { exact: true })).toHaveValue(unitId);
  await page.getByRole("button", { name: "Salvar colaboradora", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pessoa fictícia Aurora", exact: true })).toBeVisible();
  await page.goto("/employees/new");
  await expect(page.getByLabel("Unidade habitual", { exact: true })).toBeVisible();
  await expect(page.locator(`#home_unit_id option[value="${unitId}"]`)).toHaveCount(0);
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", await page.locator("body").evaluate(el => el.clientWidth));
});

test("weekly draft repetition complete arithmetic and persistence", async ({ page }) => {
  await login(page);
  await page.goto("/employees/new");
  await page.getByLabel("Nome da colaboradora").fill("Pessoa fictícia horários");
  await page.getByRole("button", { name: "Salvar colaboradora", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pessoa fictícia horários", exact: true })).toBeVisible();
  const monday = page.getByRole("group", { name: "Segunda-feira", exact: true });
  await monday.getByLabel("Situação").selectOption("working");
  await monday.getByLabel("Entrada", { exact: true }).fill("08:00");
  await page.getByRole("button", { name: "Salvar horários habituais", exact: true }).click();
  await expect(page.getByText("Rascunho salvo. Há dias pendentes ou horários incompletos.")).toBeVisible();
  await page.reload();
  await expect(monday.getByLabel("Entrada", { exact: true })).toHaveValue("08:00");
  await monday.getByLabel("Saída", { exact: true }).fill("17:00");
  await monday.getByLabel("Início do intervalo", { exact: true }).fill("12:00");
  await monday.getByLabel("Fim do intervalo", { exact: true }).fill("13:00");
  for (const day of ["Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]) await page.getByRole("checkbox", { name: day, exact: true }).check();
  await page.getByRole("button", { name: "Aplicar aos dias escolhidos", exact: true }).click();
  for (const day of ["Sábado", "Domingo"]) await page.getByRole("group", { name: day, exact: true }).getByLabel("Situação").selectOption("non_working");
  await expect(page.getByText("Total semanal previsto: 40h 00min", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Salvar horários habituais", exact: true }).click();
  await expect(page.getByText("Horários habituais salvos. Semana completa.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Total semanal previsto: 40h 00min", { exact: true })).toBeVisible();
  await monday.getByLabel("Saída", { exact: true }).fill("07:00");
  await page.getByRole("button", { name: "Salvar horários habituais", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "A saída deve ser posterior à entrada" })).toBeVisible();
});

test("operational proxy rejects unknown destinations methods filters and unsafe writes", async ({ page }) => {
  await login(page);
  const request = page.request;
  expect((await request.get("/api/v1/units?unexpected=1")).status()).toBe(422);
  expect((await request.get("/api/v1/units?page=1&page=2")).status()).toBe(422);
  expect((await request.get("/api/v1/units/not-a-uuid")).status()).toBe(404);
  expect((await request.get("/api/v1/units/00000000-0000-0000-0000-000000000000/employees?without_home_unit=true")).status()).toBe(422);
  expect((await request.delete("/api/v1/units")).status()).toBe(405);
  expect((await request.post("/api/v1/units", { data: { name: "Fictícia" } })).status()).toBe(403);
  expect((await request.patch("/api/v1/units/00000000-0000-0000-0000-000000000000", { data: { active: false } })).status()).toBe(403);
  expect((await request.put("/api/v1/employees/00000000-0000-0000-0000-000000000000/work-patterns", { data: { days: [] } })).status()).toBe(403);
  expect((await request.post("/api/v1/units", { headers: { ...headers, Origin: "https://untrusted.invalid" }, data: { name: "Fictícia" } })).status()).toBe(403);
  expect((await request.post("/api/v1/units", { headers, data: { name: "x".repeat(4096) } })).status()).toBe(413);
});
