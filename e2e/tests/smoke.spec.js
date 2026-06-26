const { test, expect } = require("@playwright/test");

test("app loads React root", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#root")).toBeVisible();
  const title = await page.title();
  expect(title.length).toBeGreaterThan(0);
});
