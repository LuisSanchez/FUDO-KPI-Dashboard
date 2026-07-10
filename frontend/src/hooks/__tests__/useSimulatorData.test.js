import { renderHook, act } from "@testing-library/react";
import useSimulatorData from "../useSimulatorData";
import * as client from "../../api/client";

jest.mock("../../api/client");

beforeEach(() => {
  jest.clearAllMocks();
});

test("handleSalesUpload sets months and clears KPIs", async () => {
  client.uploadSales.mockResolvedValue({ months: ["2026-02", "2026-03"] });
  const { result } = renderHook(() => useSimulatorData());

  await act(async () => {
    await result.current.handleSalesUpload(new File(["x"], "s.xlsx"));
  });

  expect(result.current.salesUploaded).toBe(true);
  expect(result.current.months).toEqual(["2026-02", "2026-03"]);
  expect(result.current.selectedMonth).toBe("2026-03");
  expect(result.current.expensesUploaded).toBe(false);
  expect(result.current.kpis).toBeNull();
});

test("handleSalesUpload sets error on failure", async () => {
  client.uploadSales.mockRejectedValue({
    response: { data: { error: "bad file" } },
  });
  const { result } = renderHook(() => useSimulatorData());

  await act(async () => {
    await expect(
      result.current.handleSalesUpload(new File(["x"], "s.xlsx")),
    ).rejects.toBeTruthy();
  });
  expect(result.current.error).toBe("bad file");
});

test("handleExpensesUpload success and 422 toast", async () => {
  client.uploadExpenses.mockResolvedValue({ total_rows: 2 });
  const { result } = renderHook(() => useSimulatorData());

  await act(async () => {
    await result.current.handleExpensesUpload(new File(["x"], "e.xlsx"));
  });
  expect(result.current.expensesUploaded).toBe(true);

  client.uploadExpenses.mockRejectedValue({
    response: { status: 422, data: { error: "date_mismatch" } },
  });
  await act(async () => {
    await expect(
      result.current.handleExpensesUpload(new File(["x"], "e.xlsx")),
    ).rejects.toBeTruthy();
  });
  expect(result.current.toast).toEqual({ error: "date_mismatch" });
});

test("runCalculate stores kpis", async () => {
  client.calculateKpis.mockResolvedValue({ ebitda: { ebitda: 1 } });
  const { result } = renderHook(() => useSimulatorData());

  act(() => {
    result.current.setSelectedMonth("2026-03");
  });

  await act(async () => {
    await result.current.runCalculate();
  });
  expect(result.current.kpis).toEqual({ ebitda: { ebitda: 1 } });
  expect(client.calculateKpis).toHaveBeenCalledWith({ month: "2026-03" });
});

test("handleReset clears state", async () => {
  client.resetSession.mockResolvedValue({});
  client.uploadSales.mockResolvedValue({ months: ["2026-03"] });
  const { result } = renderHook(() => useSimulatorData());

  await act(async () => {
    await result.current.handleSalesUpload(new File(["x"], "s.xlsx"));
  });
  await act(async () => {
    await result.current.handleReset();
  });
  expect(result.current.salesUploaded).toBe(false);
  expect(result.current.months).toEqual([]);
  expect(result.current.selectedMonth).toBe("");
});
