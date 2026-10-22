/**
 * OfferPath – Central API Client
 * Manages JWT tokens, HTTP requests, and visual notifications.
 */

const API_BASE = (window.location.port === "5000" || window.location.port === "5001")
  ? "" 
  : "http://localhost:5000";

const api = {
  getToken() {
    return localStorage.getItem("offerpath_token");
  },

  setToken(token) {
    localStorage.setItem("offerpath_token", token);
  },

  getUser() {
    const raw = localStorage.getItem("offerpath_user");
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("offerpath_user", JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem("offerpath_token");
    localStorage.removeItem("offerpath_user");
  },

  isAuthenticated() {
    return Boolean(this.getToken());
  },

  getHeaders(isJson = true) {
    const headers = {};
    if (isJson) {
      headers["Content-Type"] = "application/json";
    }
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
    
    // Default headers
    if (!options.isFormData) {
      options.headers = {
        ...this.getHeaders(true),
        ...(options.headers || {})
      };
    } else {
      const headers = this.getHeaders(false);
      options.headers = {
        ...headers,
        ...(options.headers || {})
      };
    }

    try {
      const response = await fetch(url, options);

      // Handle session expiration
      if (response.status === 401) {
        this.clearAuth();
        const currentPath = window.location.pathname;
        if (!currentPath.includes("login") && !currentPath.includes("register") && currentPath !== "/") {
          this.showToast("Session expired. Please log in again.", "error");
          setTimeout(() => {
            window.location.href = "/login";
          }, 1200);
        }
        const data = await response.json().catch(() => ({ error: "Unauthorized" }));
        throw new Error(data.error || "Session expired");
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.error || `HTTP error ${response.status}`);
      }

      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body)
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body)
    });
  },

  patch(endpoint, body) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  },

  uploadFile(endpoint, formData) {
    return this.request(endpoint, {
      method: "POST",
      body: formData,
      isFormData: true
    });
  },

  showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    const icon = type === "success" ? "✓" : (type === "error" ? "✕" : "ℹ");
    toast.innerHTML = `<span><strong>${icon}</strong></span><span>${message}</span>`;
    
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 400);
    }, 3500);
  }
};
