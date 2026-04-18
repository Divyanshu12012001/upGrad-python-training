// api.js — Shared API client replacing localStorage logic
const API_BASE = 'http://localhost:5000/api';

const Auth = {
  getUserId: () => parseInt(sessionStorage.getItem('userId') || '0'),
  getUserName: () => sessionStorage.getItem('userName') || 'Learner',
  getToken: () => sessionStorage.getItem('token') || '',
  setUser: (id, name, token) => {
    sessionStorage.setItem('userId', id);
    sessionStorage.setItem('userName', name);
    sessionStorage.setItem('token', token);
  },
  clear: () => sessionStorage.clear(),
  isLoggedIn: () => !!sessionStorage.getItem('token'),
  redirectIfNotLoggedIn: () => {
    if (!sessionStorage.getItem('token')) {
      window.location.href = 'login.html';
      return true;
    }
    return false;
  }
};

const Api = {
  _headers() {
    const h = { 'Content-Type': 'application/json' };
    const token = Auth.getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  },
  async get(path) {
    const res = await fetch(`${API_BASE}${path}`, { headers: this._headers() });
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return res.json();
  },
  async post(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: this._headers(),
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
    return res.json();
  },
  async put(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: this._headers(),
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`PUT ${path} failed: ${res.status}`);
    return res.json();
  },
  async del(path) {
    const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers: this._headers() });
    return res.ok;
  }
};
