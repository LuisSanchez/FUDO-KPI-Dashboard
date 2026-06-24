/**
 * Central axios instance for simulator API (SOLID: single HTTP adapter).
 * Do NOT set baseURL in dev — CRA proxy handles /api via setupProxy.js.
 */
import axios from "axios";

const client = axios.create({
  headers: { Accept: "application/json" },
});

export async function getAuthConfig() {
  const { data } = await client.get("/api/auth/config/");
  return data;
}

export async function getAuthMe() {
  const { data } = await client.get("/api/auth/me/");
  return data;
}

export async function uploadSales(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/api/upload-sales/", form);
  return data;
}

export async function uploadExpenses(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/api/upload-expenses/", form);
  return data;
}

export async function calculate(params = {}) {
  const { data } = await client.post("/api/calculate/", params);
  return data;
}

export async function resetSession() {
  const { data } = await client.post("/api/reset/");
  return data;
}

export default client;
