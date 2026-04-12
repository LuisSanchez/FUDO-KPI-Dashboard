import { useState, useCallback } from "react";
import axios from "axios";
import { CURRENT_MONTH } from "../utils/formatters";

const useDownloadExcel = (selectedMonth, onError) => {
  const [excelLoading, setExcelLoading] = useState(false);

  const downloadExcel = useCallback(async (categoria) => {
    setExcelLoading(true);
    try {
      const params = { categoria };
      if (selectedMonth && selectedMonth !== "all")
        params.month = selectedMonth;

      const res = await axios.get("/api/report/excel/", {
        params,
        responseType: "blob",
      });

      const url = URL.createObjectURL(
        new Blob([res.data], {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }),
      );
      const a = document.createElement("a");
      a.href = url;
      const month =
        selectedMonth && selectedMonth !== "all"
          ? selectedMonth
          : CURRENT_MONTH;
      a.download = `ventas-${categoria.toLowerCase()}-${month}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (_) {
      onError(`Error al generar el Excel de ${categoria}`);
    } finally {
      setExcelLoading(false);
    }
  }, [selectedMonth, onError]);

  return { downloadExcel, excelLoading };
};

export default useDownloadExcel;
