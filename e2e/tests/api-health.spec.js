const { test, expect } = require("@playwright/test");

const API = process.env.API_URL || "http://localhost:8000";

test.describe("API health", () => {
  test("reset endpoint responds", async ({ request }) => {
    const resp = await request.post(`${API}/api/reset/`);
    expect([200, 404, 405]).toContain(resp.status());
  });
});
