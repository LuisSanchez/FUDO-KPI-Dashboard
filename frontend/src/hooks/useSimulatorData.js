import { useCallback, useState } from "react";
import { calculateKpis, resetSession, uploadExpenses, uploadSales } from "../api/client";

/**
 * Centralizes upload / KPI / month selection state extracted from App.js (SRP).
 */
export default function useSimulatorData() {
  const [salesUploaded, setSalesUploaded] = useState(false);
  const [expensesUploaded, setExpensesUploaded] = useState(false);
  const [months, setMonths] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState("");
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const handleSalesUpload = useCallback(async (file) => {
    setLoading(true);
    setError(null);
    try {
      const data = await uploadSales(file);
      setSalesUploaded(true);
      if (data.months) {
        setMonths(data.months);
        setSelectedMonth(data.months[data.months.length - 1] || "");
      }
      // Re-uploading sales clears expenses on backend
      setExpensesUploaded(false);
      setKpis(null);
      return data;
    } catch (err) {
      setError(err?.response?.data?.error || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const handleExpensesUpload = useCallback(async (file) => {
    setLoading(true);
    setError(null);
    try {
      const data = await uploadExpenses(file);
      setExpensesUploaded(true);
      return data;
    } catch (err) {
      const code = err?.response?.status;
      if (code === 422) {
        setToast(err?.response?.data || { error: "date_mismatch" });
      }
      setError(err?.response?.data?.error || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const runCalculate = useCallback(
    async (extra = {}) => {
      setLoading(true);
      try {
        const data = await calculateKpis({ month: selectedMonth, ...extra });
        setKpis(data);
        return data;
      } catch (err) {
        setError(err?.response?.data?.error || err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [selectedMonth]
  );

  const handleReset = useCallback(async () => {
    await resetSession();
    setSalesUploaded(false);
    setExpensesUploaded(false);
    setMonths([]);
    setSelectedMonth("");
    setKpis(null);
  }, []);

  return {
    salesUploaded,
    expensesUploaded,
    months,
    selectedMonth,
    setSelectedMonth,
    kpis,
    loading,
    error,
    setError,
    toast,
    setToast,
    handleSalesUpload,
    handleExpensesUpload,
    runCalculate,
    handleReset,
  };
}
