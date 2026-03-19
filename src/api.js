import axios from 'axios';

// In production, VITE_API_URL should point to the deployed backend (e.g. https://api.example.com)
const backendURL = import.meta.env.VITE_API_URL || '';

const API = axios.create({
  baseURL: backendURL ? `${backendURL}/api` : '/api',
  timeout: 15000,
});

// Separate instance for auth routes (not under /api prefix)
const AuthAPI = axios.create({
  baseURL: backendURL ? `${backendURL}/auth` : '/auth',
  timeout: 15000,
});

// Attach token from localStorage on every request (both instances)
function addAuthHeader(config) {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}
API.interceptors.request.use(addAuthHeader);
AuthAPI.interceptors.request.use(addAuthHeader);

// On 401, clear token and redirect to login
API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────
export const loginUser = (username, password) =>
  AuthAPI.post('/login', { username, password }).then(r => r.data);

export const registerUser = (data) =>
  AuthAPI.post('/register', data).then(r => r.data);

export const fetchCurrentUser = () =>
  AuthAPI.get('/me').then(r => r.data);

export const seedAdmin = () =>
  AuthAPI.post('/seed-admin').then(r => r.data);

// ─── Dashboard ──────────────────────────────────
export const fetchStats = (params) => API.get('/stats', { params }).then(r => r.data);

// ─── Schools ────────────────────────────────────
export const fetchSchools = (params) => API.get('/schools', { params }).then(r => r.data);
export const fetchSchool = (id) => API.get(`/schools/${id}`).then(r => r.data);
export const createSchool = (data) => API.post('/schools', data).then(r => r.data);
export const updateFacility = (schoolId, data) => API.put(`/schools/${schoolId}/facility`, data).then(r => r.data);

// ─── Students ───────────────────────────────────
export const fetchStudents = (params) => API.get('/students', { params }).then(r => r.data);
export const createStudent = (data) => API.post('/students', data).then(r => r.data);
export const fetchStudentRisk = (id) => API.get(`/students/${id}/risk`).then(r => r.data);

// ─── Teachers ───────────────────────────────────
export const fetchTeachers = (params) => API.get('/teachers', { params }).then(r => r.data);
export const createTeacher = (data) => API.post('/teachers', data).then(r => r.data);

// ─── Feedback ───────────────────────────────────
export const fetchFeedbacks = (params) => API.get('/feedbacks', { params }).then(r => r.data);
export const createFeedback = (data) => API.post('/feedbacks', data).then(r => r.data);

// ─── AI ─────────────────────────────────────────
export const sendNLQuery = (query) => API.post('/query', { query }).then(r => r.data);
export const fetchAttendanceStats = () => API.get('/attendance-stats').then(r => r.data);

// ─── Data Ingestion ─────────────────────────────
export const ingestCSV = (file) => {
  const form = new FormData();
  form.append('file', file);
  return API.post('/ingest/csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export const ingestJSON = (file) => {
  const form = new FormData();
  form.append('file', file);
  return API.post('/ingest/json', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export default API;
