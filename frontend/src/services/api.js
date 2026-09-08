/** API client - thin fetch wrapper around the FastAPI backend.
 *
 * The dev server proxies /api and /uploads, so all requests stay relative
 * (works from any host/preview origin).
 */
const TOKEN_KEY = 'ner_token';

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

function detailMessage(body) {
  if (!body) return 'Request failed';
  if (typeof body === 'string') return body;
  if (body.detail) {
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
    return JSON.stringify(body.detail);
  }
  return 'Request failed';
}

async function request(path, { method = 'GET', body, headers = {}, form = false } = {}) {
  const opts = { method, headers: { ...headers } };
  const token = getToken();
  if (token) opts.headers.Authorization = `Bearer ${token}`;

  if (form) {
    opts.body = body; // FormData
  } else if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, opts);
  } catch {
    throw new ApiError('Network error - check your connection', 0);
  }

  const data = await parseBody(response);
  if (!response.ok) {
    throw new ApiError(detailMessage(data), response.status, data);
  }
  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  del: (path) => request(path, { method: 'DELETE' }),
  postForm: (path, formData) => request(path, { method: 'POST', body: formData, form: true }),

  async login(email, password) {
    const data = await this.post('/api/auth/login', { email, password });
    setToken(data.token);
    return data.user;
  },

  async register(payload) {
    const data = await this.post('/api/auth/register', payload);
    setToken(data.token);
    return data.user;
  },

  logout() {
    clearToken();
  },
};

/** Report list / map use these - images are served by the backend. */
export const imageUrl = (url) => (url ? url : null);
