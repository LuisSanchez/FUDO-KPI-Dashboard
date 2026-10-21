import { renderHook, act } from "@testing-library/react";
import { useTour } from "../useTour";
import { driver } from "driver.js";

vi.mock("driver.js", () => {
  const instance = { drive: vi.fn(), destroy: vi.fn() };
  return {
    __esModule: true,
    driver: vi.fn(() => instance),
  };
});

vi.mock("driver.js/dist/driver.css", () => ({}));

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  // re-bind instance methods after clearAllMocks
  const instance = { drive: vi.fn(), destroy: vi.fn() };
  driver.mockImplementation(() => instance);
});

test("startTour drives when elements exist", () => {
  document.body.innerHTML = `
    <div data-tour="sales-upload"></div>
    <div data-tour="expenses-upload"></div>
  `;
  const { result } = renderHook(() => useTour(false));
  act(() => {
    result.current.startTour();
  });
  expect(driver).toHaveBeenCalled();
  const instance = driver.mock.results[0].value;
  expect(instance.drive).toHaveBeenCalled();
});

test("startTour with bothUploaded builds extended tour", () => {
  document.body.innerHTML = `
    <div data-tour="sales-upload"></div>
    <div data-tour="expenses-upload"></div>
    <div data-tour="appbar-tables"></div>
    <div data-tour="pdf-button"></div>
    <div data-tour="help-button"></div>
  `;
  const { result } = renderHook(() => useTour(true));
  act(() => {
    result.current.startTour();
  });
  expect(driver).toHaveBeenCalled();
});
