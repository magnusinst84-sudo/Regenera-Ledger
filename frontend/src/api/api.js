import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Attach auth token to every request ───────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Auto-logout on 401 ────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ─────────────────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────────────────
// POST /api/auth/login       → { access_token, user }
export const login = (credentials) => api.post('/api/auth/login', credentials);

// POST /api/auth/register    → { access_token, user }
export const register = (userData) => api.post('/api/auth/register', userData);

// GET  /api/auth/me          → { id, email, name, role, company_name }
export const getMe = () => api.get('/api/auth/me');

// ─────────────────────────────────────────────────────────
// DASHBOARD
// ─────────────────────────────────────────────────────────
// GET /api/dashboard/stats   → { esg_score, co2_reported, risk_flags, farmer_matches, recent_analyses[] }
export const getDashboardStats = () => api.get('/api/dashboard/stats');

// GET /api/audit/            → { logs[], count }
export const getAuditLog = () => api.get('/api/audit/');

// ─────────────────────────────────────────────────────────
// ESG ANALYSIS
// ─────────────────────────────────────────────────────────
// POST /api/analysis/esg     (multipart) → { id, report_id, result }
export const analyzeESG = (formData) =>
  api.post('/api/analysis/esg', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

// GET  /api/analysis/history → { results[], count }
export const getAnalysisHistory = () => api.get('/api/analysis/history');

// ─────────────────────────────────────────────────────────
// SCOPE 3
// ─────────────────────────────────────────────────────────
// POST /api/analysis/scope3  (multipart) → { id, report_id, result }
export const analyzeScope3 = (formData) =>
  api.post('/api/analysis/scope3', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

// ─────────────────────────────────────────────────────────
// CARBON GAP
// ─────────────────────────────────────────────────────────
// POST /api/analysis/carbon-gap → { id, result }
export const analyzeGap = (data) => api.post('/api/analysis/carbon-gap', data);

// ─────────────────────────────────────────────────────────
// FARMER MATCHING
// ─────────────────────────────────────────────────────────
// POST /api/matching/         → { id, carbon_gap, matches[], total_farmers_evaluated }
export const matchFarmer = (data) => api.post('/api/matching/', data);

// GET  /api/farmer/all → { farmers: [], count: 0 }
export const getFarmers = () => api.get('/api/farmer/all');

// ─────────────────────────────────────────────────────────
// FARMER PROFILE
// ─────────────────────────────────────────────────────────
// GET  /api/farmer/profile   → farmer profile object
export const getFarmerProfile = () => api.get('/api/farmer/profile');

// PUT  /api/farmer/profile   → updated profile object
export const updateFarmerProfile = (data) => api.put('/api/farmer/profile', data);

// GET  /api/farmer/dashboard → { credits_earned, earnings, active_matches, acres, credibility, credit_history[] }
export const getFarmerDashboard = () => api.get('/api/farmer/dashboard');

// POST /api/farmer/estimate  → { id, farmer_profile_id, result }
export const estimateFarmer = (data) => api.post('/api/farmer/estimate', data);

// DELETE /api/farmer/profile/{id} → { status, message }
export const removeFarmer = (id) => api.delete(`/api/farmer/profile/${id}`);

export default api;
