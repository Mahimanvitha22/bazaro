import axios from "axios";
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api" });
api.interceptors.request.use(c => { const t = localStorage.getItem("token"); if (t) c.headers.Authorization = `Token ${t}`; return c; });
export const errText = e => { const d = e.response?.data; return d?.detail || (d && Object.values(d).flat().join(" ")) || "Something went wrong. Try again."; };
export default api;
