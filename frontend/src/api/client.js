import axios from "axios";

// Do NOT set axios.defaults.baseURL in development — CRA proxy needs relative /api.
const api = axios.create({ withCredentials: true });

export async function fetchAuthConfig() {
  const { data } = await api.get("/api/auth/config/");
  return data;
}

export async function fetchMe() {
  const { data } = await api.get("/api/auth/me/");
  return data;
}

export async function loginWithGoogle(credential) {
  const { data } = await api.post("/api/auth/google/", { credential });
  return data;
}

export async function logout() {
  const { data } = await api.post("/api/auth/logout/");
  return data;
}

export async function uploadSales(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/upload-sales/", form);
  return data;
}

export async function uploadExpenses(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/upload-expenses/", form);
  return data;
}

export async function calculateKpis(payload) {
  const { data } = await api.post("/api/calculate/", payload);
  return data;
}

export async function resetSession() {
  const { data } = await api.post("/api/reset/");
  return data;
}

export default api;
