import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MonthHistory from "../MonthHistory";
import { fetchMonthHistory, saveMonthSueldos } from "../../api/client";
import { CLP } from "../../utils/formatters";

jest.mock("../../api/client", () => ({
  fetchMonthHistory: jest.fn(),
  importMonthArchive: jest.fn(),
  saveMonthSueldos: jest.fn(),
}));

const september = {
  month: "2026-09",
  tickets: 545,
  cobrado_sin_iva: 6223834,
  cobrado: 7404362,
  gastos_sin_sueldos: 8113386,
  sueldos_fudo: 0,
  sueldos_usados: 1300000,
  ebitda: 6223834 - 8113386 - 1300000,
  resultado: 6223834 - 8113386 - 1300000 - 726539,
  comision_uber: 726539,
  comision_fuente: "pdf",
  delta_cobrado_pct: null,
  delta_resultado: null,
  channels: { caja: 0, walker: 0, pedidos_ya: 0, uber_eats: 2779960, otro: 0 },
  uber: {
    carta: 4272910,
    descuentos: 1492950,
    cobrado: 2779960,
    comision_neta: 722790,
    tasa_servicio: 860120,
    neto_estimado: 1919840,
  },
  uber_pdf: { neto: 655892, tasa: -864581, anuncios: -330468, ajustes: -918264 },
};

beforeEach(() => {
  fetchMonthHistory.mockResolvedValue({
    default_sueldos: 1300000,
    archive_available: true,
    commission_rate: 0.26,
    months: [september],
  });
  saveMonthSueldos.mockResolvedValue({});
});

test("typed payroll updates the preview and the table waits for save", async () => {
  const user = userEvent.setup();
  render(<MonthHistory />);

  expect(await screen.findByText("Mes a evaluar: Sep 2026")).toBeTruthy();
  expect(screen.getAllByText(CLP(655892)).length).toBeGreaterThan(0);
  expect(screen.getByText("Liquidación, sin IVA")).toBeTruthy();

  const input = screen.getByRole("textbox", { name: "Sueldos del mes" });
  await waitFor(() => expect(input.value).toBe("1300000"));
  const saved = september.ebitda;
  expect(screen.getAllByText(CLP(saved)).length).toBeGreaterThan(0);

  await user.clear(input);
  await user.type(input, "2000000");

  const preview = 6223834 - 8113386 - 2000000;
  expect(screen.getAllByText(CLP(preview)).length).toBeGreaterThan(0);
  expect(screen.getAllByText(CLP(saved)).length).toBeGreaterThan(0);
  expect(saveMonthSueldos).not.toHaveBeenCalled();

  await user.click(screen.getByRole("button", { name: "Usar este sueldo" }));
  await waitFor(() =>
    expect(saveMonthSueldos).toHaveBeenCalledWith({ month: "2026-09", sueldos: 2000000 }),
  );
});

test("a month with remuneraciones starts from the file payment", async () => {
  fetchMonthHistory.mockResolvedValue({
    default_sueldos: 1300000,
    archive_available: true,
    months: [
      {
        ...september,
        month: "2026-02",
        sueldos_fudo: 1954158,
        previred: 453579,
        sueldos_usados: 1954158,
        sueldos_sugerido: 1954158,
        tiene_remuneraciones: true,
        gastos_sin_sueldos: 10580634,
        ebitda: 4038499 - 10580634 - 1954158,
      },
    ],
  });
  render(<MonthHistory />);
  expect(await screen.findByText("Mes a evaluar: Febrero 2026")).toBeTruthy();
  const input = screen.getByRole("textbox", { name: "Sueldos del mes" });
  await waitFor(() => expect(input.value).toBe("1954158"));
  expect(screen.getByText("Previred, aparte: $453.579", { exact: false })).toBeTruthy();
  expect(screen.getByRole("button", { name: `Volver a ${CLP(1954158)}` })).toBeTruthy();
});

test("volver al supuesto borra el sueldo guardado", async () => {
  fetchMonthHistory.mockResolvedValue({
    default_sueldos: 1300000,
    archive_available: false,
    months: [{ ...september, sueldos_usados: 2000000, ebitda: -3889552 }],
  });
  const user = userEvent.setup();
  render(<MonthHistory />);
  await screen.findByText("Mes a evaluar: Sep 2026");
  await user.click(screen.getByRole("button", { name: `Volver a ${CLP(1300000)}` }));
  await waitFor(() =>
    expect(saveMonthSueldos).toHaveBeenCalledWith({ month: "2026-09", reset: true }),
  );
});
