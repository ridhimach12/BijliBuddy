import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('bijlibuddy_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function resolveBackendOrigin() {
  if (API_BASE_URL.startsWith('http')) {
    return API_BASE_URL.replace(/\/api\/?$/, '');
  }
  return '';
}

export function resolveAssetUrl(path) {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${resolveBackendOrigin()}${path}`;
}

export const authApi = {
  register: (data) => apiClient.post('/auth/register', data).then((r) => r.data),
  login: (data) => apiClient.post('/auth/login', data).then((r) => r.data),
  me: () => apiClient.get('/auth/me').then((r) => r.data),
  demoAccounts: () => apiClient.get('/auth/demo-accounts').then((r) => r.data),
};

export const publicApi = {
  categories: () => apiClient.get('/public/categories').then((r) => r.data),
  localities: () => apiClient.get('/public/localities').then((r) => r.data),
  electricians: (params) => apiClient.get('/public/electricians', { params }).then((r) => r.data),
  electricianDetail: (id) => apiClient.get(`/public/electricians/${id}`).then((r) => r.data),
  notifications: () => apiClient.get('/public/notifications').then((r) => r.data),
  markNotificationsRead: () => apiClient.post('/public/notifications/read-all').then((r) => r.data),
};

export const mlApi = {
  analyzeIssue: (data) => apiClient.post('/ml/analyze-issue', data).then((r) => r.data),
  estimatePrice: (data) => apiClient.post('/ml/estimate-price', data).then((r) => r.data),
  matchElectricians: (data) => apiClient.post('/ml/match-electricians', data).then((r) => r.data),
  modelMetrics: () => apiClient.get('/ml/model-metrics').then((r) => r.data),
};

export const customerApi = {
  getProfile: () => apiClient.get('/customers/profile').then((r) => r.data),
  updateProfile: (data) => apiClient.put('/customers/profile', data).then((r) => r.data),
  uploadImage: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient
      .post('/customers/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data);
  },
  createServiceRequest: (data) => apiClient.post('/customers/service-requests', data).then((r) => r.data),
  listServiceRequests: () => apiClient.get('/customers/service-requests').then((r) => r.data),
  createBooking: (data) => apiClient.post('/customers/bookings', data).then((r) => r.data),
  listBookings: () => apiClient.get('/customers/bookings').then((r) => r.data),
  submitReview: (bookingId, data) =>
    apiClient.post(`/customers/bookings/${bookingId}/review`, data).then((r) => r.data),
};

export const electricianApi = {
  getProfile: () => apiClient.get('/electricians/profile').then((r) => r.data),
  updateProfile: (data) => apiClient.put('/electricians/profile', data).then((r) => r.data),
  getDashboard: () => apiClient.get('/electricians/dashboard').then((r) => r.data),
  respondBooking: (bookingId, data) =>
    apiClient.post(`/electricians/bookings/${bookingId}/respond`, data).then((r) => r.data),
  startBooking: (bookingId) =>
    apiClient.post(`/electricians/bookings/${bookingId}/start`).then((r) => r.data),
  completeBooking: (bookingId, data) =>
    apiClient.post(`/electricians/bookings/${bookingId}/complete`, data).then((r) => r.data),
};

export const bookingApi = {
  getDetail: (bookingId) => apiClient.get(`/bookings/${bookingId}`).then((r) => r.data),
  cancel: (bookingId, reason) => apiClient.post(`/bookings/${bookingId}/cancel`, { reason }).then((r) => r.data),
  sandboxPay: (bookingId, paymentMethod) =>
    apiClient.post(`/bookings/${bookingId}/sandbox-payment`, { payment_method: paymentMethod }).then((r) => r.data),
};

export const adminApi = {
  overview: () => apiClient.get('/admin/overview').then((r) => r.data),
  demandAnalytics: (horizonDays = 7) =>
    apiClient.get('/admin/demand-analytics', { params: { horizon_days: horizonDays } }).then((r) => r.data),
  leaderboard: () => apiClient.get('/admin/leaderboard').then((r) => r.data),
  listElectricians: () => apiClient.get('/admin/electricians').then((r) => r.data),
  verifyElectrician: (id, data) =>
    apiClient.post(`/admin/electricians/${id}/verify`, data).then((r) => r.data),
};
