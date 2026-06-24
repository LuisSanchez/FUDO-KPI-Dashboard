const { test, expect } = require("@playwright/test");

test.describe("OMP simulator smoke", () => {
  test("landing loads React root", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
    await expect(page.locator("#root")).toBeVisible();
  });
});
