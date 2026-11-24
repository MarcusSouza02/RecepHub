import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/e2e", workers: 1, fullyParallel: false, timeout: 60000,
  expect: { timeout: 10000 },
  forbidOnly: Boolean(process.env.CI), retries: 0, reporter: "list",
  use: { baseURL: "http://127.0.0.1:3180", trace: "off", screenshot: "off" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } } },
  ],
  webServer: { command: "npm run start -- --hostname 127.0.0.1 --port 3180",
    url: "http://127.0.0.1:3180/login", reuseExistingServer: false, timeout: 120000,
    env: { AUTH_ORIGIN: "http://127.0.0.1:3180", AUTH_SECURE_COOKIE: "false",
      BACKEND_INTERNAL_URL: process.env.E2E_BACKEND_URL ?? "http://127.0.0.1:3181" } },
});
