import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";
const origin = "http://127.0.0.1:3180";
const headers = { Origin: origin, "X-RecepHub-CSRF": "1" };
const credentials = { username: "e2e.demo", password: "Browser-fictional-password-123!" };
test.beforeEach(() => {
  execFileSync("docker", ["exec", "recephub-sprint02-api-test", "python", "-m", "tests.e2e_admin", "reset"], { stdio: "pipe" });
});
async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill(credentials.username);
  await page.getByLabel("Senha", { exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL("/dashboard");
}
test("anonymous and forged cookie cannot access private page", async ({ page, context }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL("/login");
  await context.addCookies([{ name: "recephub_session", value: "a".repeat(43), domain: "127.0.0.1", path: "/" }]);
  await page.goto("/dashboard");
  await expect(page).toHaveURL("/login");
});
test("real login HttpOnly cookie logout and history", async ({ page, context }) => {
  await login(page);
  const privateResponse = await page.goto("/dashboard?view=older");
  expect(privateResponse?.headers()["cache-control"]).toContain("no-store");
  await page.goto("/dashboard?view=current");
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  const cookie = (await context.cookies()).find(c => c.name === "recephub_session");
  expect(cookie?.httpOnly).toBe(true);
  expect(cookie?.sameSite).toBe("Lax");
  expect(await page.evaluate(() => document.cookie)).not.toContain("recephub_session");
  await page.getByRole("button", { name: "Sair", exact: true }).filter({ visible: true }).click();
  await expect(page).toHaveURL("/login");
  await page.goBack();
  await expect(page).toHaveURL("/login");
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toHaveCount(0);
  await page.goto("/dashboard");
  await expect(page).toHaveURL("/login");
});
test("independent desktop/mobile sessions survive other device logout", async ({ page, browser }) => {
  await login(page);
  const second = await browser.newContext({ baseURL: origin, viewport: { width: 390, height: 844 } });
  try {
    const other = await second.newPage();
    await login(other);
    await page.getByRole("button", { name: "Sair", exact: true }).filter({ visible: true }).click();
    await expect(page).toHaveURL("/login");
    await other.reload();
    await expect(other).toHaveURL("/dashboard");
  } finally { await second.close(); }
});
test("invalid credentials and rate limiting are distinct", async ({ page, request }) => {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).fill(credentials.username);
  await page.getByLabel("Senha", { exact: true }).fill("Wrong-fictional-password-123!");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Usuário ou senha inválidos." })).toBeVisible();
  for (let i=0;i<4;i++) expect((await request.post("/api/v1/auth/login", { headers, data: { ...credentials, username: "unknown.user" } })).status()).toBe(401);
  const limited = await request.post("/api/v1/auth/login", { headers, data: credentials });
  expect(limited.status()).toBe(429);
  expect(Number(limited.headers()["retry-after"])).toBeGreaterThan(0);
  await page.getByLabel("Senha", { exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Muitas tentativas" })).toBeVisible();
});
test("proxy allowlist csrf body limit and readiness", async ({ request }) => {
  expect((await request.get("/api/v1/admin")).status()).toBe(404);
  expect((await request.get("/api/v1/auth/login")).status()).toBe(405);
  expect((await request.post("/api/v1/auth/login", { data: credentials })).status()).toBe(403);
  expect((await request.post("/api/v1/auth/login", { headers: { ...headers, Origin: "https://evil.example" }, data: credentials })).status()).toBe(403);
  expect((await request.post("/api/v1/auth/login", { headers, data: { ...credentials, password: "a".repeat(4096) } })).status()).toBe(413);
  expect((await request.get("/api/v1/health/ready")).status()).toBe(200);
});
test("responsive layout keyboard and manifest", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Usuário", { exact: true }).focus();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Senha", { exact: true })).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await login(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("link", { name: "Pular para o conteúdo" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#conteudo")).toBeFocused();
  await page.getByRole("button", { name: "Sair", exact: true }).filter({ visible: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL("/login");
  const manifest = await page.request.get("/manifest.webmanifest");
  expect(manifest.status()).toBe(200);
  const manifestData = await manifest.json();
  expect(manifestData.name).toBe("RecepHub");
  for (const icon of manifestData.icons) expect((await page.request.get(icon.src)).status()).toBe(200);
});

test("monitor detects real expiration when the page regains focus", async ({ page }) => {
  await login(page);
  execFileSync("docker", ["exec", "recephub-sprint02-api-test", "python", "-m", "tests.e2e_admin", "expire"], { stdio: "pipe" });
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page).toHaveURL("/login");
});
test("monitor reports simulated outage without claiming logout", async ({ page }) => {
  await page.route("**/api/v1/auth/session", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"simulated outage"}' }));
  await login(page);
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("status").filter({ hasText: "Não foi possível verificar sua sessão" })).toBeVisible();
  await expect(page).toHaveURL("/dashboard");
});
test("device clock skew does not expire a valid session", async ({ page }) => {
  await page.addInitScript(() => { const realNow = Date.now.bind(Date); Date.now = () => realNow() + 4 * 60 * 60 * 1000; });
  await login(page);
  const revalidation = page.waitForResponse(response => response.url().endsWith("/api/v1/auth/session"));
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  expect((await revalidation).status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await expect(page).toHaveURL("/dashboard");
});

test("session timer expires without background polling", async ({ page }) => {
  await page.clock.install();
  await login(page);
  execFileSync("docker", ["exec", "recephub-sprint02-api-test", "python", "-m", "tests.e2e_admin", "expire"], { stdio: "pipe" });
  let sessionRequests = 0;
  page.on("request", request => { if (request.url().endsWith("/api/v1/auth/session")) sessionRequests++; });
  await page.clock.runFor(61000);
  expect(sessionRequests).toBe(0);
  await page.clock.fastForward(2 * 60 * 60 * 1000);
  await expect(page).toHaveURL("/login");
});
test("failed logout keeps the private page and reports failure", async ({ page }) => {
  await login(page);
  await page.route("**/api/v1/auth/logout", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"simulated outage"}' }));
  await page.getByRole("button", { name: "Sair", exact: true }).filter({ visible: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Não foi possível sair" }).filter({ visible: true })).toBeVisible();
  await expect(page).toHaveURL("/dashboard");
});
