import { useState } from "react";
import axios from "axios";
import { fmtMonth, CURRENT_MONTH } from "../utils/formatters";

const useDownloadPdf = (selectedMonth, onError) => {
  const [pdfLoading, setPdfLoading] = useState(false);

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? { month: selectedMonth }
          : {};
      const res = await axios.get("/api/report/pdf/", {
        params,
        responseType: "blob",
      });
      const url = URL.createObjectURL(
        new Blob([res.data], { type: "application/pdf" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download =
        selectedMonth && selectedMonth !== "all"
          ? `reporte-${selectedMonth}.pdf`
          : `reporte-financiero-${fmtMonth(CURRENT_MONTH)}.pdf`;
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
