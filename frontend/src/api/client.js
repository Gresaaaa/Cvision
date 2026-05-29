import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
});

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

function formatValidationLocation(loc) {
  if (!Array.isArray(loc)) return "";
  return loc
    .filter((part) => !["body", "query", "path"].includes(String(part)))
    .map((part) => {
      if (typeof part === "number") {
        return `item ${part + 1}`;
      }
      return String(part).replaceAll("_", " ");
    })
    .join(" -> ");
}

export function getErrorMessage(error, fallback = "Something went wrong.") {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const message = item?.msg || item?.message || String(item);
        const location = formatValidationLocation(item?.loc);
        return location ? `${location}: ${message}` : message;
      })
      .join(". ");
  }
  return detail || error?.message || fallback;
}

export function toAssetUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  try {
    const base = new URL(api.defaults.baseURL, window.location.origin);
    return new URL(path, base.origin).toString();
  } catch {
    return path;
  }
}

export default api;
