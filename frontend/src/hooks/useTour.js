import { useCallback, useEffect, useRef } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";

const TOUR_KEY = "fudo_tour_v1";

function buildSteps(bothUploaded) {
  const steps = [
    {
      element: '[data-tour="sales-upload"]',
      popover: {
        title: "① Carga tus ventas",
        description:
          "Arrastra o selecciona el archivo <strong>Adiciones</strong> exportado desde FUDO. Los gráficos de ventas, ranking de productos y la tendencia diaria se activarán al instante.",
        side: "bottom",
        align: "start",
      },
    },
    {
      element: '[data-tour="expenses-upload"]',
      popover: {
        title: "② Carga tus gastos",
        description:
          "Sube el archivo <strong>Gastos</strong> de FUDO. Esto activa el cálculo de EBITDA, CMV y el análisis de break-even para saber cuánto necesitas vender para ser rentable.",
        side: "bottom",
        align: "start",
      },
    },
  ];

  if (bothUploaded) {
    steps.push(
      {
        element: '[data-tour="appbar-tables"]',
        popover: {
          title: "③ Tablas detalladas",
          description:
            "<strong>Ventas:</strong> detalle por producto con CMV y margen bruto.<br/>" +
            "<strong>Precios:</strong> precio neto promedio y costo por producto.<br/>" +
            "<strong>Gastos:</strong> cada gasto categorizado con su estado de pago.",
          side: "bottom",
          align: "end",
        },
      },
      {
        element: '[data-tour="pdf-button"]',
        popover: {
          title: "④ Reporte PDF",
          description:
            "Genera y descarga un resumen financiero en PDF con KPIs, análisis de break-even y ventas por producto. Ideal para compartir con socios o llevar al contador.",
          side: "bottom",
          align: "end",
        },
      },
    );
  }

  steps.push({
    element: '[data-tour="help-button"]',
    popover: {
      title: bothUploaded ? "⑤ Ayuda y fórmulas" : "③ Ayuda y fórmulas",
      description:
        "Abre el manual para entender cada métrica: IVA (19%), CMV, EBITDA, break-even y cómo se calculan. " +
        "También puedes reiniciar este tour en cualquier momento con el ícono <strong>Explorar</strong> del AppBar.",
      side: "bottom",
      align: "end",
    },
  });

  return steps;
}

/**
 * Manages the Driver.js onboarding tour.
 *
 * - Auto-starts once per browser (localStorage key `fudo_tour_v1`).
 * - Skipping or finishing the tour saves the key so it won't auto-start again.
 * - `startTour()` lets users restart it manually from an AppBar icon.
 *
 * @param {boolean} bothUploaded - Whether both sales and expenses are uploaded.
 *   When true, steps 3-4 (tables, PDF) are included in the tour.
 */
export function useTour(bothUploaded) {
  const driverRef = useRef(null);

  const startTour = useCallback(() => {
    // Destroy any running instance before starting a new one
    driverRef.current?.destroy();

    const d = driver({
      showProgress: true,
      progressText: "{{current}} / {{total}}",
      nextBtnText: "Siguiente →",
      prevBtnText: "← Anterior",
      doneBtnText: "¡Listo!",
      allowClose: true,
      overlayOpacity: 0.6,
      steps: buildSteps(bothUploaded),
      onDestroyed: () => {
        localStorage.setItem(TOUR_KEY, "1");
      },
    });

    driverRef.current = d;
    d.drive();
  }, [bothUploaded]);

  // Auto-start only on first visit (key not set in localStorage)
  useEffect(() => {
    if (localStorage.getItem(TOUR_KEY)) return;
    const timer = setTimeout(startTour, 700);
    return () => clearTimeout(timer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { startTour };
}
