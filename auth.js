/**
 * OfferPath – Authentication Controller
 * Handles user login, registration, auth guards, and profile updates.
 */

document.addEventListener("DOMContentLoaded", () => {
  initAuthUI();
  setupLoginForm();
  setupRegisterForm();
  setupLogoutBtn();
});

function initAuthUI() {
  const user = api.getUser();
  const path = window.location.pathname;
  const isAuthPage = path.includes("login") || path.includes("register") || path === "/";

  // Auth guard: If user not logged in and visiting protected page
  if (!api.isAuthenticated() && !isAuthPage) {
    window.location.href = "/login";
    return;
  }

  // If already authenticated and visiting landing/login/register, redirect to dashboard
  if (api.isAuthenticated() && isAuthPage) {
    window.location.href = "/dashboard";
    return;
  }

  // Populate user badge in header if element exists
  const userBadge = document.getElementById("header-user-badge");
  const userName = document.getElementById("header-user-name");
  const userAvatar = document.getElementById("header-user-avatar");

  if (user && userName) {
    userName.textContent = user.full_name || user.username;
    if (userAvatar) {
      userAvatar.textContent = (user.full_name || user.username).charAt(0).toUpperCase();
    }
  }
}

function setupLoginForm() {
  const form = document.getElementById("login-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector("button[type='submit']");
    const originalText = submitBtn.innerHTML;

    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
      api.showToast("Please provide both email/username and password.", "error");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner" style="width:16px;height:16px;"></span> Signing in...`;

      const response = await api.post("/api/auth/login", {
        identifier: email,
        password: password
      });

      if (response.success && response.token) {
        api.setToken(response.token);
        api.setUser(response.user);
        api.showToast("Login successful! Redirecting...", "success");
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 600);
      }
    } catch (err) {
      api.showToast(err.message || "Invalid credentials. Please try again.", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

function setupRegisterForm() {
  const form = document.getElementById("register-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector("button[type='submit']");
    const originalText = submitBtn.innerHTML;

    const fullName = document.getElementById("reg-fullname").value.trim();
    const username = document.getElementById("reg-username").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const targetRole = document.getElementById("reg-role").value.trim();

    if (!username || !email || !password) {
      api.showToast("Please fill in all required fields.", "error");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner" style="width:16px;height:16px;"></span> Creating account...`;

      const response = await api.post("/api/auth/register", {
        full_name: fullName,
        username: username,
        email: email,
        password: password,
        target_role: targetRole || "Software Engineer"
      });

      if (response.success && response.token) {
        api.setToken(response.token);
        api.setUser(response.user);
        api.showToast("Account created successfully! Redirecting to dashboard...", "success");
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 800);
      }
    } catch (err) {
      api.showToast(err.message || "Failed to register account.", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

function setupLogoutBtn() {
  const logoutBtn = document.getElementById("logout-btn");
  if (!logoutBtn) return;

  logoutBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await api.post("/api/auth/logout", {});
    } catch {
      // Ignore network errors on logout
    }
    api.clearAuth();
    api.showToast("Logged out successfully.", "info");
    setTimeout(() => {
      window.location.href = "/login";
    }, 400);
  });
}
