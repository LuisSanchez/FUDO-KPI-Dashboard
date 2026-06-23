// @ts-check
const { defineConfig, devices } = require("@playwright/test");

/**
 * Frontend E2E — runs against CRA (default :3000) with API proxied to Django.
 *
 * Local:
 *   Terminal 1: cd backend && DEBUG=True python3 manage.py runserver
 *   Terminal 2: cd frontend && npm start
 *   Terminal 3: cd frontend && npm run test:e2e
 *
 * CI / smoke only (SPA shell, no backend):
 *   E2E_BASE_URL=http://127.0.0.1:3000 npm run test:e2e -- --grep @smoke
 */
const baseURL = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";

module.exports = defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  timeout: 60_000,
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
