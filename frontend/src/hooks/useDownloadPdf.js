import { useState } from "react";
import axios from "axios";

const useDownloadPdf = (selectedMonth, onError, months = []) => {
  const [pdfLoading, setPdfLoading] = useState(false);

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    try {
      const specificMonth =
        selectedMonth && selectedMonth !== "all" ? selectedMonth : null;
      const params = specificMonth ? { month: specificMonth } : {};
      const res = await axios.get("/api/report/pdf/", {
        params,
        responseType: "blob",
      });
      const url = URL.createObjectURL(
        new Blob([res.data], { type: "application/pdf" }),
      );
      const a = document.createElement("a");
      a.href = url;
      if (specificMonth) {
        a.download = `reporte-${specificMonth}.pdf`;
      } else if (months.length === 1) {
        a.download = `reporte-${months[0]}.pdf`;
      } else if (months.length > 1) {
        a.download = `reporte-${months[0]}_a_${months[months.length - 1]}.pdf`;
      } else {
        a.download = "reporte-financiero.pdf";
      }
      a.click();
      URL.revokeObjectURL(url);
    } catch (_) {
      onError("Error al generar el reporte PDF");
    } finally {
      setPdfLoading(false);
    }
  };

  return { handleDownloadPdf, pdfLoading };
};

export default useDownloadPdf;
