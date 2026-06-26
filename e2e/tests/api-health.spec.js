const { test, expect } = require("@playwright/test");

const API = process.env.E2E_API_URL || "http://localhost:8000";

test("reset endpoint responds", async ({ request }) => {
  const res = await request.post(`${API}/api/reset/`);
  expect([200, 403]).toContain(res.status());
});

test("auth config is public", async ({ request }) => {
  const res = await request.get(`${API}/api/auth/config/`);
  // 404 on older deploys without auth is acceptable
  expect([200, 404]).toContain(res.status());
  if (res.status() === 200) {
    const body = await res.json();
    expect(body).toHaveProperty("oauth_enabled");
  }
});
