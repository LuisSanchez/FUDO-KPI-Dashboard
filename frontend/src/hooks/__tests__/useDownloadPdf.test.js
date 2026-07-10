import { renderHook, act } from "@testing-library/react";
import useDownloadPdf from "../useDownloadPdf";
import axios from "axios";

jest.mock("axios");

beforeEach(() => {
  jest.clearAllMocks();
  global.URL.createObjectURL = jest.fn(() => "blob:url");
  global.URL.revokeObjectURL = jest.fn();
});

test("downloads PDF with specific month filename", async () => {
  axios.get.mockResolvedValue({ data: new Blob(["%PDF"]) });
  const onError = jest.fn();
  const { result } = renderHook(() =>
    useDownloadPdf("2026-03", onError, ["2026-03"]),
  );

  await act(async () => {
    await result.current.handleDownloadPdf();
  });
  expect(axios.get).toHaveBeenCalledWith(
    "/api/report/pdf/",
    expect.objectContaining({ params: { month: "2026-03" } }),
  );
  expect(result.current.pdfLoading).toBe(false);
});

test("range filename when multiple months and all selected", async () => {
  axios.get.mockResolvedValue({ data: new Blob(["%PDF"]) });
  const { result } = renderHook(() =>
    useDownloadPdf("all", jest.fn(), ["2026-01", "2026-03"]),
  );
  await act(async () => {
    await result.current.handleDownloadPdf();
  });
  expect(axios.get).toHaveBeenCalledWith(
    "/api/report/pdf/",
    expect.objectContaining({ params: {} }),
  );
});

test("calls onError on failure", async () => {
  axios.get.mockRejectedValue(new Error("fail"));
  const onError = jest.fn();
  const { result } = renderHook(() => useDownloadPdf("2026-03", onError, []));
  await act(async () => {
    await result.current.handleDownloadPdf();
  });
  expect(onError).toHaveBeenCalledWith("Error al generar el reporte PDF");
});
