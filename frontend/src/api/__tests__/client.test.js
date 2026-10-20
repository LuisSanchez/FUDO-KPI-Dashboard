import api, {
  fetchAuthConfig,
  fetchMe,
  loginWithGoogle,
  logout,
  uploadSales,
  uploadExpenses,
  calculateKpis,
  resetSession,
  fetchMonthHistory,
  importMonthArchive,
  saveMonthSueldos,
  askDataChat,
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

test("fetchMonthHistory GETs history", async () => {
  axios.get.mockResolvedValue({ data: { months: [] } });
  const data = await fetchMonthHistory();
  expect(axios.get).toHaveBeenCalledWith("/api/history/");
  expect(data.months).toEqual([]);
});

test("importMonthArchive POSTs the archive import", async () => {
  axios.post.mockResolvedValue({ data: { months: ["2026-09"] } });
  const data = await importMonthArchive();
  expect(axios.post).toHaveBeenCalledWith("/api/history/import-archive/");
  expect(data.months).toEqual(["2026-09"]);
});

test("saveMonthSueldos POSTs the payroll override", async () => {
  axios.post.mockResolvedValue({ data: { sueldos: 1300000 } });
  const data = await saveMonthSueldos({ month: "2026-09", sueldos: 1300000 });
  expect(axios.post).toHaveBeenCalledWith("/api/history/sueldos/", {
    month: "2026-09",
    sueldos: 1300000,
  });
  expect(data.sueldos).toBe(1300000);
});

test("askDataChat POSTs the conversation", async () => {
  axios.post.mockResolvedValue({ data: { reply: "Listo", consultas: [] } });
  const messages = [{ role: "user", content: "¿y septiembre?" }];
  const data = await askDataChat(messages);
  expect(axios.post).toHaveBeenCalledWith(
    "/api/chat/",
    { messages },
    { timeout: 180000 },
  );
  expect(data.reply).toBe("Listo");
});

test("resetSession POSTs reset", async () => {
  axios.post.mockResolvedValue({ data: { message: "ok" } });
  await resetSession();
  expect(axios.post).toHaveBeenCalledWith("/api/reset/");
});

test("default export is axios instance", () => {
  expect(api).toBeTruthy();
});
