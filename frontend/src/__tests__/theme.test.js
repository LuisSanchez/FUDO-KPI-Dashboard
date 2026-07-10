import createAppTheme from "../theme";

test("createAppTheme dark mode palette", () => {
  const theme = createAppTheme("dark");
  expect(theme.palette.mode).toBe("dark");
  expect(theme.palette.primary.main).toBe("#F97316");
  expect(theme.palette.background.default).toBe("#0F172A");
});

test("createAppTheme light mode palette", () => {
  const theme = createAppTheme("light");
  expect(theme.palette.mode).toBe("light");
  expect(theme.palette.background.paper).toBe("#FFFFFF");
});
