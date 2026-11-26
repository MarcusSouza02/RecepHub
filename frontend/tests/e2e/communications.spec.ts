import { execFileSync } from "node:child_process";
import { expect, test } from "@playwright/test";

test.beforeEach(() => { execFileSync("docker", ["exec", process.env.E2E_BACKEND_CONTAINER ?? "recephub-sprint06-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" }); });

test("manual communication is editable and email preserves accents", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill("e2e.demo");
  await page.getByLabel("Senha", { exact: true }).fill("Browser-fictional-password-123!");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL("/dashboard");
  await page.goto("/communications");
  await page.getByLabel("Informações para o comunicado", { exact: true }).fill("Atenção: São João, horário às 08h.");
  await page.getByRole("button", { name: "Preparar comunicado", exact: true }).click();
  await expect(page.getByLabel("Corpo do comunicado", { exact: true })).toHaveValue(/São João/);
  await page.getByLabel("Assunto", { exact: true }).fill("Aviso revisado — São João");
  const link = page.getByRole("link", { name: "Abrir rascunho de e-mail", exact: true });
  await expect(link).toHaveAttribute("href", /subject=Aviso%20revisado/);
  expect(decodeURIComponent((await link.getAttribute("href"))!)).toContain("São João");
  await page.getByLabel("Corpo do comunicado", { exact: true }).fill("Atenção São João. ".repeat(300));
  await expect(link).toHaveCount(0);
  await expect(page.getByText(/nenhum conteúdo foi cortado/)).toBeVisible();
  await page.evaluate(() => { Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: () => Promise.reject(new Error("Fictional denial")) } }); });
  await page.getByRole("button", { name: "Copiar corpo", exact: true }).click();
  await expect(page.getByText(/Selecione o texto no campo e copie manualmente/)).toBeVisible();
});
