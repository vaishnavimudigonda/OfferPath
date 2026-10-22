/**
 * OfferPath – Applications List & Management Controller
 * Full CRUD, search, filter, and modal interactions.
 */

let applicationsList = [];

document.addEventListener("DOMContentLoaded", () => {
  if (!api.isAuthenticated()) return;
  loadApplications();
  setupSearchAndFilters();
  setupAddEditModal();
});

async function loadApplications() {
  const tableBody = document.getElementById("applications-table-body");
  if (!tableBody) return;

  try {
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem;"><span class="spinner" style="border-color: #cbd5e1; border-top-color: var(--primary);"></span> Loading applications...</td></tr>`;
    
    const status = document.getElementById("filter-status")?.value || "";
    const search = document.getElementById("search-input")?.value || "";

    let endpoint = "/api/applications";
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (search) params.append("search", search);
    if (params.toString()) endpoint += `?${params.toString()}`;

    const res = await api.get(endpoint);
    applicationsList = res.applications || [];
    renderApplicationsTable(applicationsList);
  } catch (err) {
    console.error("Failed to load applications:", err);
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--danger);">Failed to load applications.</td></tr>`;
  }
}

function renderApplicationsTable(apps) {
  const tableBody = document.getElementById("applications-table-body");
  const countBadge = document.getElementById("apps-count-badge");
  if (!tableBody) return;

  if (countBadge) countBadge.textContent = `${apps.length} Applications`;

  if (apps.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7">
          <div class="empty-state">
            <div class="empty-icon">📁</div>
            <div class="empty-title">No applications found</div>
            <p>Track your job search by adding an application or modifying your filters.</p>
            <button class="btn btn-primary btn-sm" style="margin-top: 1rem;" onclick="openAddModal()">+ Add New Application</button>
          </div>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = apps.map(app => {
    const dateFormatted = app.application_date ? new Date(app.application_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "N/A";
    const statusClass = `badge-${(app.status || "Saved").toLowerCase()}`;

    return `
      <tr>
        <td style="font-weight: 700; color: var(--gray-900);">${escapeHtml(app.company_name)}</td>
        <td style="font-weight: 600;">${escapeHtml(app.job_title)}</td>
        <td><span class="badge ${statusClass}">${escapeHtml(app.status)}</span></td>
        <td>${dateFormatted}</td>
        <td>${escapeHtml(app.location || "Remote")}</td>
        <td>${escapeHtml(app.salary || "—")}</td>
        <td style="text-align: right;">
          <div style="display: inline-flex; gap: 0.4rem;">
            <button class="btn btn-secondary btn-sm" title="View Details" onclick="viewAppDetails(${app.id})">Details</button>
            <button class="btn btn-secondary btn-sm" title="Edit" onclick="openEditModal(${app.id})">Edit</button>
            <button class="btn btn-secondary btn-sm" style="color: var(--danger);" title="Delete" onclick="deleteApp(${app.id}, '${escapeHtml(app.company_name)}')">Delete</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function setupSearchAndFilters() {
  const searchInput = document.getElementById("search-input");
  const statusFilter = document.getElementById("filter-status");

  let debounceTimer;
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadApplications();
      }, 300);
    });
  }

  if (statusFilter) {
    statusFilter.addEventListener("change", () => {
      loadApplications();
    });
  }
}

function setupAddEditModal() {
  const form = document.getElementById("app-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const appId = document.getElementById("form-app-id").value;
    const isEdit = Boolean(appId);

    const payload = {
      company_name: document.getElementById("form-company").value.trim(),
      job_title: document.getElementById("form-title").value.trim(),
      status: document.getElementById("form-status").value,
      application_date: document.getElementById("form-date").value,
      job_url: document.getElementById("form-url").value.trim(),
      location: document.getElementById("form-location").value.trim(),
      salary: document.getElementById("form-salary").value.trim(),
      job_description: document.getElementById("form-jd").value.trim(),
      notes: document.getElementById("form-notes").value.trim()
    };

    if (!payload.company_name || !payload.job_title) {
      api.showToast("Company name and Job title are required.", "error");
      return;
    }

    try {
      if (isEdit) {
        await api.put(`/api/applications/${appId}`, payload);
        api.showToast("Application updated successfully.", "success");
      } else {
        await api.post("/api/applications", payload);
        api.showToast("Application created successfully.", "success");
      }

      closeModal("app-modal");
      form.reset();
      loadApplications();
    } catch (err) {
      api.showToast(err.message || "Operation failed.", "error");
    }
  });
}

function openAddModal() {
  const form = document.getElementById("app-form");
  if (!form) return;
  form.reset();
  document.getElementById("form-app-id").value = "";
  document.getElementById("modal-form-title").textContent = "Add New Job Application";
  document.getElementById("form-date").valueAsDate = new Date();
  openModal("app-modal");
}

function openEditModal(appId) {
  const app = applicationsList.find(a => a.id === appId);
  if (!app) return;

  document.getElementById("form-app-id").value = app.id;
  document.getElementById("form-company").value = app.company_name || "";
  document.getElementById("form-title").value = app.job_title || "";
  document.getElementById("form-status").value = app.status || "Saved";
  document.getElementById("form-date").value = app.application_date ? app.application_date.split("T")[0] : "";
  document.getElementById("form-url").value = app.job_url || "";
  document.getElementById("form-location").value = app.location || "";
  document.getElementById("form-salary").value = app.salary || "";
  document.getElementById("form-jd").value = app.job_description || "";
  document.getElementById("form-notes").value = app.notes || "";

  document.getElementById("modal-form-title").textContent = `Edit Application – ${app.company_name}`;
  openModal("app-modal");
}

async function deleteApp(appId, companyName) {
  if (!confirm(`Are you sure you want to delete the application for "${companyName}"? This action cannot be undone.`)) {
    return;
  }

  try {
    await api.delete(`/api/applications/${appId}`);
    api.showToast("Application deleted.", "info");
    loadApplications();
  } catch (err) {
    api.showToast(err.message || "Failed to delete application.", "error");
  }
}

async function viewAppDetails(appId) {
  const app = applicationsList.find(a => a.id === appId);
  if (!app) return;

  const content = document.getElementById("details-modal-content");
  if (!content) return;

  content.innerHTML = `
    <div style="margin-bottom: 1rem;">
      <span class="badge badge-${app.status.toLowerCase()}">${escapeHtml(app.status)}</span>
    </div>
    <h3 style="font-size: 1.35rem; margin-bottom: 0.2rem;">${escapeHtml(app.job_title)}</h3>
    <h4 style="font-size: 1.05rem; color: var(--primary); margin-bottom: 1.25rem;">${escapeHtml(app.company_name)}</h4>

    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.25rem; font-size: 0.9rem;">
      <div><strong>📍 Location:</strong> ${escapeHtml(app.location || "Remote")}</div>
      <div><strong>💰 Salary:</strong> ${escapeHtml(app.salary || "Not stated")}</div>
      <div><strong>📅 Date:</strong> ${app.application_date || "N/A"}</div>
      <div><strong>🔗 Posting:</strong> ${app.job_url ? `<a href="${escapeHtml(app.job_url)}" target="_blank" rel="noopener">Job Link ↗</a>` : "None"}</div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h5 style="margin-bottom: 0.35rem;">Notes & Follow-ups</h5>
      <p style="background: var(--gray-50); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--gray-200); font-size: 0.88rem;">
        ${escapeHtml(app.notes || "No notes yet.")}
      </p>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h5 style="margin-bottom: 0.35rem;">Job Description</h5>
      <div style="max-height: 200px; overflow-y: auto; background: var(--gray-50); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--gray-200); font-size: 0.85rem; white-space: pre-wrap;">
        ${escapeHtml(app.job_description || "No job description text provided.")}
      </div>
    </div>

    <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem;">
      <a href="/resume-analysis?appId=${app.id}" class="btn btn-primary btn-sm">
        🔍 Analyze Resume Against This Job
      </a>
      <a href="/interview?appId=${app.id}" class="btn btn-secondary btn-sm">
        ✨ Generate Interview Prep
      </a>
    </div>
  `;

  openModal("details-modal");
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
