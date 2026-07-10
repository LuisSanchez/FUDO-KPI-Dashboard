import api, {
  fetchAuthConfig,
  fetchMe,
  loginWithGoogle,
  logout,
  uploadSales,
  uploadExpenses,
  calculateKpis,
  resetSession,
} from "../client";

jest.mock("axios", () => {
  const mock = {
    create: jest.fn(() => mock),
    get: jest.fn(),
    post: jest.fn(),
    defaults: {},
  };
  return mock;
});

const axios = require("axios");

beforeEach(() => {
  jest.clearAllMocks();
});

test("fetchAuthConfig GETs config endpoint", async () => {
  axios.get.mockResolvedValue({ data: { oauth_enabled: false } });
  const data = await fetchAuthConfig();
  expect(axios.get).toHaveBeenCalledWith("/api/auth/config/");
  expect(data.oauth_enabled).toBe(false);
});

test("fetchMe GETs me endpoint", async () => {
  axios.get.mockResolvedValue({ data: { authenticated: false } });
  const data = await fetchMe();
  expect(axios.get).toHaveBeenCalledWith("/api/auth/me/");
  expect(data.authenticated).toBe(false);
});

test("loginWithGoogle POSTs credential", async () => {
  axios.post.mockResolvedValue({ data: { authenticated: true } });
  const data = await loginWithGoogle("tok");
  expect(axios.post).toHaveBeenCalledWith("/api/auth/google/", { credential: "tok" });
  expect(data.authenticated).toBe(true);
});

test("logout POSTs logout", async () => {
  axios.post.mockResolvedValue({ data: { ok: true } });
  await logout();
  expect(axios.post).toHaveBeenCalledWith("/api/auth/logout/");
});

test("uploadSales POSTs FormData", async () => {
  axios.post.mockResolvedValue({ data: { months: ["2026-03"] } });
  const file = new File(["x"], "sales.xlsx");
  const data = await uploadSales(file);
  expect(axios.post).toHaveBeenCalled();
  const [url, body] = axios.post.mock.calls[0];
  expect(url).toBe("/api/upload-sales/");
  expect(body).toBeInstanceOf(FormData);
  expect(data.months).toEqual(["2026-03"]);
});

test("uploadExpenses POSTs FormData", async () => {
  axios.post.mockResolvedValue({ data: { total_rows: 1 } });
  await uploadExpenses(new File(["x"], "exp.xlsx"));
  expect(axios.post.mock.calls[0][0]).toBe("/api/upload-expenses/");
});

test("calculateKpis POSTs payload", async () => {
  axios.post.mockResolvedValue({ data: { ebitda: {} } });
  await calculateKpis({ month: "2026-03" });
  expect(axios.post).toHaveBeenCalledWith("/api/calculate/", { month: "2026-03" });
});

test("resetSession POSTs reset", async () => {
  axios.post.mockResolvedValue({ data: { message: "ok" } });
  await resetSession();
  expect(axios.post).toHaveBeenCalledWith("/api/reset/");
});

test("default export is axios instance", () => {
  expect(api).toBeTruthy();
});
