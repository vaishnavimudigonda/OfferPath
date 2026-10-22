/**
 * OfferPath – Gemini AI Interview Prep Controller
 * Question generation, category filtering, and response management.
 */

let allGeneratedQuestions = [];
let currentCategoryFilter = "All";
let currentDifficultyFilter = "All";

document.addEventListener("DOMContentLoaded", () => {
  if (!api.isAuthenticated()) return;
  initInterviewPage();
  setupInterviewForm();
  setupFilterTabs();
});

async function initInterviewPage() {
  await Promise.all([
    loadApplicationsDropdown(),
    loadResumeAutofill()
  ]);

  const urlParams = new URLSearchParams(window.location.search);
  const appId = urlParams.get("appId");
  if (appId) {
    const select = document.getElementById("select-interview-app");
    if (select) {
      select.value = appId;
      handleInterviewAppSelect(appId);
    }
  }
}

async function loadApplicationsDropdown() {
  const select = document.getElementById("select-interview-app");
  if (!select) return;

  try {
    const res = await api.get("/api/applications");
    if (res.success && res.applications.length > 0) {
      res.applications.forEach(app => {
        const opt = document.createElement("option");
        opt.value = app.id;
        opt.textContent = `${app.company_name} – ${app.job_title}`;
        opt.dataset.title = app.job_title;
        opt.dataset.jd = app.job_description || "";
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.warn("Could not load applications for interview prep:", err);
  }
}

async function loadResumeAutofill() {
  try {
    const res = await api.get("/api/resume/my-resumes");
    if (res.success && res.resumes.length > 0) {
      // Fetch latest resume full text
      const latestResumeId = res.resumes[0].id;
      const detailRes = await api.get(`/api/resume/${latestResumeId}`);
      if (detailRes.success && detailRes.resume.extracted_text) {
        const resumeTextarea = document.getElementById("interview-resume-text");
        if (resumeTextarea && !resumeTextarea.value) {
          resumeTextarea.value = detailRes.resume.extracted_text;
        }
      }
    }
  } catch (err) {
    console.warn("Could not autofill resume:", err);
  }
}

function handleInterviewAppSelect(appId) {
  const select = document.getElementById("select-interview-app");
  const opt = select.querySelector(`option[value="${appId}"]`);
  if (!opt) return;

  const titleInput = document.getElementById("interview-job-title");
  const jdInput = document.getElementById("interview-jd-text");

  if (titleInput && opt.dataset.title) titleInput.value = opt.dataset.title;
  if (jdInput && opt.dataset.jd) jdInput.value = opt.dataset.jd;
}

function setupInterviewForm() {
  const form = document.getElementById("interview-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("interview-job-title").value.trim() || "Software Engineer";
    const jd = document.getElementById("interview-jd-text").value.trim();
    const resume = document.getElementById("interview-resume-text").value.trim();
    const skillsRaw = document.getElementById("interview-skills").value.trim();
    const submitBtn = document.getElementById("generate-questions-btn");
    const errorBanner = document.getElementById("gemini-error-banner");

    if (!jd) {
      api.showToast("Job description is required to generate tailored questions.", "error");
      return;
    }

    if (errorBanner) errorBanner.style.display = "none";

    const skills = skillsRaw ? skillsRaw.split(",").map(s => s.trim()).filter(Boolean) : [];

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner" style="width:18px;height:18px;"></span> Generating Questions with Gemini AI...`;

      const res = await api.post("/api/interview/generate", {
        job_title: title,
        job_description: jd,
        resume_text: resume,
        skills: skills
      });

      if (res.success && res.questions) {
        allGeneratedQuestions = res.questions;
        api.showToast(`Generated ${allGeneratedQuestions.length} interview questions!`, "success");
        renderQuestions();
        document.getElementById("questions-results-container")?.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      if (errorBanner) {
        errorBanner.style.display = "block";
        document.getElementById("gemini-error-message").textContent = err.message || "Failed to call Gemini AI.";
      }
      api.showToast(err.message || "Failed to generate interview questions.", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `✨ Generate Interview Questions with Google Gemini`;
    }
  });
}

function setupFilterTabs() {
  const categoryTabs = document.querySelectorAll(".category-tab-btn");
  categoryTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      categoryTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentCategoryFilter = tab.dataset.category || "All";
      renderQuestions();
    });
  });

  const diffSelect = document.getElementById("filter-difficulty-select");
  if (diffSelect) {
    diffSelect.addEventListener("change", (e) => {
      currentDifficultyFilter = e.target.value;
      renderQuestions();
    });
  }
}

function renderQuestions() {
  const container = document.getElementById("questions-list-container");
  const countDisplay = document.getElementById("filtered-questions-count");
  if (!container) return;

  let filtered = allGeneratedQuestions;

  if (currentCategoryFilter !== "All") {
    filtered = filtered.filter(q => q.category.toLowerCase() === currentCategoryFilter.toLowerCase());
  }

  if (currentDifficultyFilter !== "All") {
    filtered = filtered.filter(q => q.difficulty.toLowerCase() === currentDifficultyFilter.toLowerCase());
  }

  if (countDisplay) {
    countDisplay.textContent = `Showing ${filtered.length} of ${allGeneratedQuestions.length} Questions`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">💡</div>
        <div class="empty-title">No questions found for this filter</div>
        <p>Try switching categories or difficulty filters above.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map((q, idx) => {
    const diffClass = (q.difficulty || "Medium").toLowerCase() === "hard" ? "badge-rejected" :
                     (q.difficulty || "Medium").toLowerCase() === "easy" ? "badge-offer" : "badge-assessment";

    return `
      <div class="card" style="margin-bottom: 1rem; border-left: 4px solid var(--primary);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span class="badge badge-saved" style="font-weight: 700;">${escapeHtml(q.category)}</span>
            <span class="badge ${diffClass}">${escapeHtml(q.difficulty)}</span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="copyQuestionText(${idx})">📋 Copy Question</button>
        </div>

        <h4 style="font-size: 1.05rem; font-weight: 700; color: var(--gray-900); margin-bottom: 0.75rem; line-height: 1.4;">
          ${escapeHtml(q.question)}
        </h4>

        ${q.interviewer_rationale ? `
          <details style="background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: var(--radius-sm); padding: 0.6rem 0.85rem; font-size: 0.85rem; margin-top: 0.5rem;">
            <summary style="font-weight: 600; color: var(--gray-700); cursor: pointer;">
              Why the interviewer asks this / What to demonstrate
            </summary>
            <p style="margin-top: 0.4rem; color: var(--gray-600); line-height: 1.45;">
              ${escapeHtml(q.interviewer_rationale)}
            </p>
          </details>
        ` : ""}
      </div>
    `;
  }).join("");
}

function copyQuestionText(index) {
  const q = allGeneratedQuestions[index];
  if (!q) return;

  const textToCopy = `[${q.category} - ${q.difficulty}]\nQuestion: ${q.question}\n\nInterviewer Evaluation Criteria: ${q.interviewer_rationale || "N/A"}`;
  navigator.clipboard.writeText(textToCopy).then(() => {
    api.showToast("Question copied to clipboard!", "success");
  }).catch(() => {
    api.showToast("Failed to copy to clipboard.", "error");
  });
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
