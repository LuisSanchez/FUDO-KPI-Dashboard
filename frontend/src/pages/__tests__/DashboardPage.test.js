import DashboardPage from "../DashboardPage";
import App from "../../App";

test("DashboardPage re-exports App shell", () => {
  expect(DashboardPage).toBe(App);
});
