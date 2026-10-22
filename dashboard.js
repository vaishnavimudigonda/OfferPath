/**
 * OfferPath – Dashboard Controller
 * Orchestrates Kanban board, Chart.js analytics, and metrics cards.
 */

let statusChartInstance = null;
let funnelChartInstance = null;
let timelineChartInstance = null;

const STATUSES = ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"];

document.addEventListener("DOMContentLoaded", () => {
  if (!api.isAuthenticated()) return;
  loadDashboardData();
  setupQuickAddForm();
});

async function loadDashboardData() {
  try {
    await Promise.all([
      loadAnalyticsData(),
      loadKanbanApplications()
    ]);
  } catch (err) {
    console.error("Dashboard data load error:", err);
    api.showToast("Could not load full dashboard data.", "error");
  }
}

async function loadAnalyticsData() {
  try {
    const res = await api.get("/api/analytics");
    if (!res.success) return;

    const metrics = res.metrics;
    document.getElementById("metric-total-apps").textContent = metrics.total_applications;
    document.getElementById("metric-in-progress").textContent = metrics.in_progress;
    document.getElementById("metric-interviews").textContent = metrics.interview_count;
    document.getElementById("metric-offers").textContent = metrics.offer_count;
    document.getElementById("metric-ats-score").textContent = metrics.average_ats_score ? `${metrics.average_ats_score}%` : "N/A";

    renderCharts(res.charts, res.has_data);
  } catch (err) {
    console.warn("Analytics error:", err);
  }
}

function renderCharts(chartsData, hasData) {
  const chartCard = document.getElementById("analytics-section");
  if (!chartCard) return;

  // 1. Status Distribution Doughnut Chart
  const statusCtx = document.getElementById("statusChart")?.getContext("2d");
  if (statusCtx) {
    if (statusChartInstance) statusChartInstance.destroy();
    
    statusChartInstance = new Chart(statusCtx, {
      type: "doughnut",
      data: {
        labels: chartsData.status_distribution.labels,
        datasets: [{
          data: chartsData.status_distribution.data,
          backgroundColor: [
            "#6366f1", // Saved
            "#0284c7", // Applied
            "#d97706", // Assessment
            "#9333ea", // Interview
            "#16a34a", // Offer
            "#dc2626"  // Rejected
          ],
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { boxWidth: 12, font: { size: 11 } } }
        },
        cutout: "68%"
      }
    });
  }

  // 2. Application Funnel Bar Chart
  const funnelCtx = document.getElementById("funnelChart")?.getContext("2d");
  if (funnelCtx) {
    if (funnelChartInstance) funnelChartInstance.destroy();

    funnelChartInstance = new Chart(funnelCtx, {
      type: "bar",
      data: {
        labels: chartsData.application_funnel.labels,
        datasets: [{
          label: "Candidates / Applications",
          data: chartsData.application_funnel.data,
          backgroundColor: ["#818cf8", "#38bdf8", "#c084fc", "#4ade80"],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0 } },
          y: { grid: { display: false } }
        }
      }
    });
  }
}

async function loadKanbanApplications() {
  const res = await api.get("/api/applications");
  if (!res.success) return;

  const applications = res.applications;
  renderKanban(applications);
}

function renderKanban(applications) {
  // Clear columns
  STATUSES.forEach(status => {
    const listEl = document.getElementById(`kanban-list-${status.toLowerCase()}`);
    const countEl = document.getElementById(`count-${status.toLowerCase()}`);
    if (listEl) listEl.innerHTML = "";
    if (countEl) countEl.textContent = "0";
  });

  const columnCounts = {};
  STATUSES.forEach(s => columnCounts[s] = 0);

  applications.forEach(app => {
    const status = app.status || "Saved";
    columnCounts[status] = (columnCounts[status] || 0) + 1;

    const listEl = document.getElementById(`kanban-list-${status.toLowerCase()}`);
    if (listEl) {
      const card = createKanbanCard(app);
      listEl.appendChild(card);
    }
  });

  // Update counts
  STATUSES.forEach(status => {
    const countEl = document.getElementById(`count-${status.toLowerCase()}`);
    if (countEl) countEl.textContent = columnCounts[status] || 0;
  });

  setupDragAndDrop();
}

function createKanbanCard(app) {
  const card = document.createElement("div");
  card.className = "kanban-card";
  card.draggable = true;
  card.dataset.id = app.id;
  card.dataset.status = app.status;

  const dateStr = app.application_date ? new Date(app.application_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "Recently";
  const salaryHtml = app.salary ? `<div class="card-meta-item"><span>💰</span><span>${escapeHtml(app.salary)}</span></div>` : "";
  const locationHtml = app.location ? `<div class="card-meta-item"><span>📍</span><span>${escapeHtml(app.location)}</span></div>` : "";

  // Build status options
  let optionsHtml = "";
  STATUSES.forEach(st => {
    optionsHtml += `<option value="${st}" ${st === app.status ? "selected" : ""}>${st}</option>`;
  });

  card.innerHTML = `
    <div class="card-company">${escapeHtml(app.company_name)}</div>
    <div class="card-title">${escapeHtml(app.job_title)}</div>
    <div class="card-meta">
      <div class="card-meta-item"><span>📅</span><span>${dateStr}</span></div>
      ${locationHtml}
      ${salaryHtml}
    </div>
    <div class="card-footer">
      <select class="status-select" onchange="handleStatusChange(${app.id}, this.value)">
        ${optionsHtml}
      </select>
      <button class="card-action-btn" title="View Details" onclick="viewApplicationDetails(${app.id})">🔍</button>
    </div>
  `;

  return card;
}

function setupDragAndDrop() {
  const cards = document.querySelectorAll(".kanban-card");
  const columns = document.querySelectorAll(".kanban-column");

  cards.forEach(card => {
    card.addEventListener("dragstart", (e) => {
      card.classList.add("dragging");
      e.dataTransfer.setData("text/plain", card.dataset.id);
      e.dataTransfer.effectAllowed = "move";
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
    });
  });

  columns.forEach(column => {
    column.addEventListener("dragover", (e) => {
      e.preventDefault();
      column.classList.add("drag-over");
      e.dataTransfer.dropEffect = "move";
    });

    column.addEventListener("dragleave", () => {
      column.classList.remove("drag-over");
    });

    column.addEventListener("drop", async (e) => {
      e.preventDefault();
      column.classList.remove("drag-over");
      
      const appId = e.dataTransfer.getData("text/plain");
      const targetStatus = column.dataset.status;

      if (!appId || !targetStatus) return;

      await handleStatusChange(appId, targetStatus);
    });
  });
}

async function handleStatusChange(appId, newStatus) {
  try {
    const res = await api.patch(`/api/applications/${appId}/status`, { status: newStatus });
    if (res.success) {
      api.showToast(`Stage updated to "${newStatus}"`, "success");
      // Reload applications and analytics
      await loadDashboardData();
    }
  } catch (err) {
    api.showToast(err.message || "Failed to update status", "error");
  }
}

function setupQuickAddForm() {
  const form = document.getElementById("quick-add-app-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const company = document.getElementById("quick-company").value.trim();
    const title = document.getElementById("quick-title").value.trim();
    const status = document.getElementById("quick-status").value;
    const salary = document.getElementById("quick-salary").value.trim();
    const location = document.getElementById("quick-location").value.trim();

    if (!company || !title) {
      api.showToast("Company name and job title are required.", "error");
      return;
    }

    try {
      const res = await api.post("/api/applications", {
        company_name: company,
        job_title: title,
        status: status || "Saved",
        salary: salary,
        location: location || "Remote"
      });

      if (res.success) {
        api.showToast("Application added to tracker!", "success");
        form.reset();
        closeModal("add-app-modal");
        await loadDashboardData();
      }
    } catch (err) {
      api.showToast(err.message || "Failed to add application.", "error");
    }
  });
}

async function viewApplicationDetails(appId) {
  try {
    const res = await api.get(`/api/applications/${appId}`);
    if (!res.success) return;

    const app = res.application;
    const modalBody = document.getElementById("details-modal-content");
    if (!modalBody) return;

    modalBody.innerHTML = `
      <div style="margin-bottom: 1.25rem;">
        <span class="badge badge-${app.status.toLowerCase()}" style="font-size:0.85rem; padding: 0.35rem 0.85rem;">
          ${escapeHtml(app.status)}
        </span>
      </div>
      <h3 style="font-size: 1.4rem; margin-bottom: 0.25rem;">${escapeHtml(app.job_title)}</h3>
      <p style="font-size: 1.1rem; color: var(--primary); font-weight: 600; margin-bottom: 1rem;">
        ${escapeHtml(app.company_name)}
      </p>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.25rem; font-size: 0.9rem;">
        <div><strong>📍 Location:</strong> ${escapeHtml(app.location || "Not specified")}</div>
        <div><strong>💰 Compensation:</strong> ${escapeHtml(app.salary || "Not specified")}</div>
        <div><strong>📅 Applied Date:</strong> ${app.application_date || "N/A"}</div>
        <div><strong>🔗 Job URL:</strong> ${app.job_url ? `<a href="${escapeHtml(app.job_url)}" target="_blank" rel="noopener">Open Link ↗</a>` : "None"}</div>
      </div>

      <div style="margin-bottom: 1.25rem;">
        <h4 style="font-size: 1rem; margin-bottom: 0.4rem;">Notes</h4>
        <p style="background: var(--gray-50); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--gray-200); font-size: 0.9rem;">
          ${escapeHtml(app.notes || "No notes added yet.")}
        </p>
      </div>

      <div style="margin-bottom: 1.25rem;">
        <h4 style="font-size: 1rem; margin-bottom: 0.4rem;">Job Description</h4>
        <div style="max-height: 180px; overflow-y: auto; background: var(--gray-50); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--gray-200); font-size: 0.85rem; white-space: pre-wrap;">
          ${escapeHtml(app.job_description || "No job description text provided.")}
        </div>
      </div>

      <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem;">
        <button class="btn btn-primary" onclick="launchAnalysisFromApp(${app.id})">
          🔍 Analyze Resume Against This Job
        </button>
        <button class="btn btn-secondary" onclick="launchInterviewFromApp(${app.id})">
          ✨ Prep Interview Questions
        </button>
      </div>
    `;

    openModal("details-modal");
  } catch (err) {
    api.showToast("Could not load application details.", "error");
  }
}

function launchAnalysisFromApp(appId) {
  window.location.href = `/resume-analysis?appId=${appId}`;
}

function launchInterviewFromApp(appId) {
  window.location.href = `/interview?appId=${appId}`;
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
