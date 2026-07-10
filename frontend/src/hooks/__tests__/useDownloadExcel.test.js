import { renderHook, act } from "@testing-library/react";
import useDownloadExcel from "../useDownloadExcel";
import axios from "axios";

jest.mock("axios");

beforeEach(() => {
  jest.clearAllMocks();
  global.URL.createObjectURL = jest.fn(() => "blob:url");
  global.URL.revokeObjectURL = jest.fn();
});

test("downloadExcel requests report with categoria and month", async () => {
  axios.get.mockResolvedValue({ data: new Blob(["xlsx"]) });
  const { result } = renderHook(() =>
    useDownloadExcel("2026-03", jest.fn()),
  );
  await act(async () => {
    await result.current.downloadExcel("Especialidades");
  });
  expect(axios.get).toHaveBeenCalledWith(
    "/api/report/excel/",
    expect.objectContaining({
      params: { categoria: "Especialidades", month: "2026-03" },
    }),
  );
});

test("downloadExcel calls onError on failure", async () => {
  axios.get.mockRejectedValue(new Error("x"));
  const onError = jest.fn();
  const { result } = renderHook(() => useDownloadExcel("all", onError));
  await act(async () => {
    await result.current.downloadExcel("Extras");
  });
  expect(onError).toHaveBeenCalledWith("Error al generar el Excel de Extras");
});
