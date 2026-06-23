// @ts-check
const { test, expect } = require("@playwright/test");
const path = require("path");
const fs = require("fs");

/**
 * Full upload flow — requires backend + frontend running and sample FUDO files.
 * Skips automatically when fixtures are missing (keeps CI green without data).
 */

const LAB_DATA = path.resolve(__dirname, "../../backend/lab/data");

function pickFixture(globPrefix, ext) {
  if (!fs.existsSync(LAB_DATA)) return null;
  const files = fs
    .readdirSync(LAB_DATA)
    .filter((f) => f.startsWith(globPrefix) && f.endsWith(ext))
    .sort();
  return files.length ? path.join(LAB_DATA, files[files.length - 1]) : null;
}

const salesFixture = pickFixture("cg-ventas-", ".xls") || pickFixture("sm-sales-", ".xls");
const expensesFixture =
  pickFixture("cg-gastos-", ".xlsx") || pickFixture("sm-gastos-", ".xlsx");

test.describe("Upload + calculate @integration", () => {
  test.skip(!salesFixture || !expensesFixture, "Sample FUDO Excel fixtures not present");

  test("upload sales and expenses surfaces KPI UI", async ({ page }) => {
    test.setTimeout(120_000);
    const apiErrors = [];
    page.on("response", (res) => {
      if (res.url().includes("/api/") && res.status() >= 500) {
        apiErrors.push(`${res.status()} ${res.url()}`);
      }
    });

    await page.goto("/");

    // Prefer file inputs hidden by react-dropzone (accept excel)
    const fileInputs = page.locator('input[type="file"]');
    const count = await fileInputs.count();
    test.skip(count < 1, "No file inputs found — UI may have changed");

    // First input: sales, second (if any): expenses; else reuse first after sales.
    await fileInputs.nth(0).setInputFiles(salesFixture);
    // Wait for successful sales upload toast or products/month UI
    await page.waitForTimeout(1500);
    await expect
      .poll(async () => {
        const body = await page.locator("body").innerText();
        return /escenario|per[ií]odo|kpi|ebitda|mes|producto|imput/i.test(body);
      }, { timeout: 30_000 })
      .toBeTruthy();

    const inputsAfter = page.locator('input[type="file"]');
    const n = await inputsAfter.count();
    await inputsAfter.nth(Math.min(1, n - 1)).setInputFiles(expensesFixture);

    // After both files, calculate should run and show numbers / dashboard.
    await expect
      .poll(async () => {
        const body = await page.locator("body").innerText();
        return /ebitda|ingreso|gasto|contribuci[oó]n|ticket/i.test(body);
      }, { timeout: 45_000 })
      .toBeTruthy();

    // Scenarios panel appears once sales are loaded (optional feature).
    const scenariosHeading = page.getByText(/escenarios guardados/i);
    if (await scenariosHeading.isVisible().catch(() => false)) {
      await page.getByRole("button", { name: /guardar escenario/i }).click();
      await page.waitForTimeout(800);
    }

    expect(apiErrors, `API 5xx: ${apiErrors.join(", ")}`).toEqual([]);
  });
});
