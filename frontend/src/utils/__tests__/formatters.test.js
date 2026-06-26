import { CLP, PCT } from "../formatters";

test("CLP formats Chilean pesos", () => {
  const s = CLP(1000);
  expect(typeof s).toBe("string");
  expect(s.length).toBeGreaterThan(0);
});

test("PCT formats percentage", () => {
  const s = PCT(0.25);
  expect(typeof s).toBe("string");
});
