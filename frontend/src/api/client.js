import axios from "axios";

// Relative /api. Vite proxies it in dev. Do not set axios.defaults.baseURL.
const api = axios.create({ withCredentials: true });

let tokenGetter = null;

export function setClerkTokenGetter(getter) {
  tokenGetter = typeof getter === "function" ? getter : null;
}

async function attachClerkToken(config) {
  if (!tokenGetter) return config;
  try {
    const token = await tokenGetter();
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    // Unsigned request. The API answers 401.
  }
  return config;
}

api.interceptors.request.use(attachClerkToken);
axios.interceptors.request.use(attachClerkToken);

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

export async function fetchMonthHistory() {
  const { data } = await api.get("/api/history/");
  return data;
}

export async function importMonthArchive() {
  const { data } = await api.post("/api/history/import-archive/");
  return data;
}

export async function saveMonthSueldos(payload) {
  const { data } = await api.post("/api/history/sueldos/", payload);
  return data;
}

export async function askDataChat(messages) {
  const { data } = await api.post("/api/chat/", { messages }, { timeout: 180000 });
  return data;
}

export async function fetchAiSettings() {
  const { data } = await api.get("/api/settings/ai/");
  return data;
}

export async function saveAiSettings(payload) {
  const { data } = await api.put("/api/settings/ai/", payload);
  return data;
}

export async function fetchOllamaModels(baseUrl) {
  const { data } = await api.get("/api/settings/ai/ollama-models/", {
    params: baseUrl ? { base_url: baseUrl } : {},
  });
  return data;
}

export default api;
