import {
  CLP,
  PCT,
  CURRENT_MONTH,
  MONTH_NAMES,
  fmtMonth,
  cmvColor,
  TIPO_COLOR,
} from "../formatters";

test("CLP formats Chilean pesos", () => {
  const s = CLP(1000);
  expect(typeof s).toBe("string");
  expect(s.length).toBeGreaterThan(0);
  expect(s).toMatch(/1.?000|1000/);
});

test("PCT formats percentage with default and custom decimals", () => {
  expect(PCT(0.25)).toBe("0.3%");
  expect(PCT(25.456, 2)).toBe("25.46%");
  expect(PCT(10, 0)).toBe("10%");
});

test("CURRENT_MONTH is YYYY-MM", () => {
  expect(CURRENT_MONTH).toMatch(/^\d{4}-\d{2}$/);
});

test("MONTH_NAMES covers all months", () => {
  expect(MONTH_NAMES["01"]).toBe("Enero");
  expect(MONTH_NAMES["12"]).toBe("Dic");
  expect(Object.keys(MONTH_NAMES)).toHaveLength(12);
});

test("fmtMonth formats year-month labels", () => {
  expect(fmtMonth("2026-03")).toBe("Marzo 2026");
  expect(fmtMonth("2025-12")).toBe("Dic 2025");
});

test("cmvColor thresholds", () => {
  expect(cmvColor(30)).toBe("success");
  expect(cmvColor(35)).toBe("success");
  expect(cmvColor(40)).toBe("warning");
  expect(cmvColor(42)).toBe("warning");
  expect(cmvColor(50)).toBe("error");
});

test("TIPO_COLOR map", () => {
  expect(TIPO_COLOR.Operacional).toBe("default");
  expect(TIPO_COLOR.Préstamo).toBe("warning");
  expect(TIPO_COLOR["Activo Fijo"]).toBe("info");
});
