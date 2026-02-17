// API Base URL configuration
// In production, the API is served from the same domain
// In development, it connects to localhost or specified URL
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// Get auth token from localStorage
function getAuthToken() {
  const user = localStorage.getItem('bb_auth_user');
  if (user) {
    try {
      const parsed = JSON.parse(user);
      return parsed.token || null;
    } catch (e) {
      return null;
    }
  }
  return null;
}

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Add auth header if token exists
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    headers,
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.detail || error.message || 'API request failed');
  }

  return response.json();
}

export const api = {
  // Auth
  login: (username, password) =>
    fetchAPI('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  
  getMe: () =>
    fetchAPI('/api/auth/me'),
  
  refreshToken: () =>
    fetchAPI('/api/auth/refresh', { method: 'POST' }),

  // Dashboard
  getDashboard: (platform = 'instagram', topN = 10) =>
    fetchAPI(`/api/dashboard?platform=${platform}&top_n=${topN}`),

  // Brands
  getBrands: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.category) queryParams.append('category', params.category);
    if (params.search) queryParams.append('search', params.search);
    return fetchAPI(`/api/brands/?${queryParams.toString()}`);
  },

  searchBrands: (query) =>
    fetchAPI(`/api/brands/search?q=${encodeURIComponent(query)}`),

  getBrand: (id) =>
    fetchAPI(`/api/brands/${id}`),

  getBrandFull: (id) =>
    fetchAPI(`/api/brands/${id}/full`),

  getBrandMetrics: (id, params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.platform) queryParams.append('platform', params.platform);
    if (params.days) queryParams.append('days', params.days);
    return fetchAPI(`/api/brands/${id}/metrics?${queryParams.toString()}`);
  },

  getBrandGrowth: (id, platform = 'instagram', days = 30) =>
    fetchAPI(`/api/brands/${id}/growth?platform=${platform}&days=${days}`),

  // Rankings
  getRankings: (params = {}) => {
    const queryParams = new URLSearchParams();
    queryParams.append('period', params.period || '7d');
    queryParams.append('platform', params.platform || 'instagram');
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    return fetchAPI(`/api/rankings/?${queryParams.toString()}`);
  },

  getTopBrands: (period = '7d', platform = 'instagram', limit = 10) =>
    fetchAPI(`/api/rankings/top?period=${period}&platform=${platform}&limit=${limit}`),

  // Metrics
  getMetrics: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.brand_id) queryParams.append('brand_id', params.brand_id);
    if (params.platform) queryParams.append('platform', params.platform);
    if (params.days) queryParams.append('days', params.days);
    return fetchAPI(`/api/metrics/?${queryParams.toString()}`);
  },

  getMetricsSummary: (days = 30) =>
    fetchAPI(`/api/metrics/summary?days=${days}`),

  // Categories
  getCategories: () =>
    fetchAPI('/api/categories'),

  // Export
  exportBrands: (format = 'csv') =>
    fetch(`${API_BASE_URL}/api/export/brands?format=${format}`, {
      headers: getAuthToken() ? { 'Authorization': `Bearer ${getAuthToken()}` } : {}
    }),

  exportMetrics: (brandId, format = 'csv') => {
    const url = brandId 
      ? `${API_BASE_URL}/api/export/metrics?brand_id=${brandId}&format=${format}`
      : `${API_BASE_URL}/api/export/metrics?format=${format}`;
    return fetch(url, {
      headers: getAuthToken() ? { 'Authorization': `Bearer ${getAuthToken()}` } : {}
    });
  },

  // Sync
  triggerSync: () =>
    fetchAPI('/api/sync', { method: 'POST' }),

  // Credits / Usage
  getCreditsUsage: (days = 30) =>
    fetchAPI(`/api/credits/usage?days=${days}`),

  getCreditsBudget: () =>
    fetchAPI('/api/credits/budget'),

  // Brand Research
  researchWebsite: (websiteUrl) =>
    fetchAPI('/api/brands/research/website', {
      method: 'POST',
      body: JSON.stringify({ website_url: websiteUrl }),
    }),

  getPendingBrands: (status) => {
    const queryParams = new URLSearchParams();
    if (status) queryParams.append('status', status);
    return fetchAPI(`/api/brands/research/pending?${queryParams.toString()}`);
  },

  approvePendingBrand: (pendingId) =>
    fetchAPI(`/api/brands/research/pending/${pendingId}/approve`, { method: 'POST' }),

  rejectPendingBrand: (pendingId) =>
    fetchAPI(`/api/brands/research/pending/${pendingId}/reject`, { method: 'POST' }),

  getUpdateLogs: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.brand_id) queryParams.append('brand_id', params.brand_id);
    if (params.days) queryParams.append('days', params.days);
    return fetchAPI(`/api/brands/research/updates?${queryParams.toString()}`);
  },
};
