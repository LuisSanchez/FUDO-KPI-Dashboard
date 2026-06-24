import { CLP, PCT } from "../formatters";

describe("formatters", () => {
  test("CLP formats numbers", () => {
    expect(typeof CLP(1000)).toBe("string");
    expect(CLP(0)).toBeTruthy();
  });

  test("PCT formats percentages", () => {
    expect(typeof PCT(25.5)).toBe("string");
  });
});
