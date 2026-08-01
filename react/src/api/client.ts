import axios from "axios";

// Vite only exposes env vars prefixed VITE_ to client code — a deliberate security boundary,
// not a naming convention we chose. Falls back to the local dev backend if unset.
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 15_000,
});
