import { renderHook, act } from "@testing-library/react";
import useDownloadExcel from "../useDownloadExcel";
import axios from "axios";

vi.mock("axios", () => {
  const mock = { get: vi.fn() };
  return { default: mock };
});

beforeEach(() => {
  vi.clearAllMocks();
  global.URL.createObjectURL = vi.fn(() => "blob:url");
  global.URL.revokeObjectURL = vi.fn();
});

test("downloadExcel requests report with categoria and month", async () => {
  axios.get.mockResolvedValue({ data: new Blob(["xlsx"]) });
  const { result } = renderHook(() =>
    useDownloadExcel("2026-03", vi.fn()),
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
  const onError = vi.fn();
  const { result } = renderHook(() => useDownloadExcel("all", onError));
  await act(async () => {
    await result.current.downloadExcel("Extras");
  });
  expect(onError).toHaveBeenCalledWith("Error al generar el Excel de Extras");
});
