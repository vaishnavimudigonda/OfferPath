/**
 * OfferPath – Resume ATS Analysis Controller
 * File uploads, TF-IDF analysis triggers, and score visualization.
 */

document.addEventListener("DOMContentLoaded", () => {
  if (!api.isAuthenticated()) return;
  initAnalysisPage();
  setupFileUpload();
  setupAnalysisForm();
});

async function initAnalysisPage() {
  await Promise.all([
    loadSavedApplicationsForDropdown(),
    loadUserResumesForDropdown()
  ]);

  // Check if an application ID was passed in query string (e.g. ?appId=12)
  const urlParams = new URLSearchParams(window.location.search);
  const appId = urlParams.get("appId");
  if (appId) {
    const selectEl = document.getElementById("select-application");
    if (selectEl) {
      selectEl.value = appId;
      handleApplicationSelect(appId);
    }
  }
}

async function loadSavedApplicationsForDropdown() {
  const select = document.getElementById("select-application");
  if (!select) return;

  try {
    const res = await api.get("/api/applications");
    if (res.success && res.applications.length > 0) {
      res.applications.forEach(app => {
        const opt = document.createElement("option");
        opt.value = app.id;
        opt.textContent = `${app.company_name} – ${app.job_title}`;
        opt.dataset.jd = app.job_description || "";
        opt.dataset.title = app.job_title || "";
        opt.dataset.company = app.company_name || "";
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.warn("Could not load applications for dropdown:", err);
  }
}

async function loadUserResumesForDropdown() {
  const select = document.getElementById("select-saved-resume");
  if (!select) return;

  try {
    const res = await api.get("/api/resume/my-resumes");
    if (res.success && res.resumes.length > 0) {
      res.resumes.forEach(r => {
        const opt = document.createElement("option");
        opt.value = r.id;
        opt.textContent = `${r.file_name} (${r.file_type.toUpperCase()})`;
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.warn("Could not load resumes dropdown:", err);
  }
}

function handleApplicationSelect(appId) {
  const select = document.getElementById("select-application");
  const selectedOption = select.querySelector(`option[value="${appId}"]`);
  if (!selectedOption) return;

  const jdText = selectedOption.dataset.jd || "";
  const title = selectedOption.dataset.title || "";
  
  const jdInput = document.getElementById("job-description-input");
  const titleInput = document.getElementById("target-title-input");

  if (jdInput && jdText) jdInput.value = jdText;
  if (titleInput && title) titleInput.value = title;
}

async function handleSavedResumeSelect(resumeId) {
  if (!resumeId) return;
  try {
    const res = await api.get(`/api/resume/${resumeId}`);
    if (res.success && res.resume.extracted_text) {
      const resumeInput = document.getElementById("resume-text-input");
      if (resumeInput) {
        resumeInput.value = res.resume.extracted_text;
        api.showToast(`Loaded "${res.resume.file_name}"`, "info");
      }
    }
  } catch (err) {
    api.showToast("Could not load resume text.", "error");
  }
}

function setupFileUpload() {
  const fileInput = document.getElementById("resume-file-input");
  const dropZone = document.getElementById("upload-dropzone");
  const fileNameDisplay = document.getElementById("uploaded-filename");

  if (!fileInput || !dropZone) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--primary)";
    dropZone.style.background = "var(--primary-light)";
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "var(--gray-300)";
    dropZone.style.background = "var(--white)";
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--gray-300)";
    dropZone.style.background = "var(--white)";

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected(fileInput.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      handleFileSelected(fileInput.files[0]);
    }
  });
}

async function handleFileSelected(file) {
  const fileNameDisplay = document.getElementById("uploaded-filename");
  if (fileNameDisplay) {
    fileNameDisplay.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-color:#6366f1;border-top-color:transparent;"></span> Parsing ${file.name}...`;
  }

  const formData = new FormData();
  formData.append("resume", file);

  try {
    const res = await api.uploadFile("/api/resume/upload", formData);
    if (res.success && res.resume) {
      const resumeTextarea = document.getElementById("resume-text-input");
      if (resumeTextarea) {
        resumeTextarea.value = res.resume.extracted_text;
      }
      if (fileNameDisplay) {
        fileNameDisplay.innerHTML = `✓ <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB) parsed successfully.`;
      }
      api.showToast("Resume parsed and loaded into analyzer!", "success");
    }
  } catch (err) {
    if (fileNameDisplay) fileNameDisplay.innerHTML = `<span style="color:var(--danger)">Failed to extract text: ${err.message}</span>`;
    api.showToast(err.message || "Failed to parse resume file.", "error");
  }
}

function setupAnalysisForm() {
  const form = document.getElementById("analysis-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const resumeText = document.getElementById("resume-text-input").value.trim();
    const jobDescription = document.getElementById("job-description-input").value.trim();
    const targetTitle = document.getElementById("target-title-input")?.value.trim() || "Target Position";
    const submitBtn = document.getElementById("run-analysis-btn");

    if (!resumeText) {
      api.showToast("Please upload or paste your resume text.", "error");
      return;
    }

    if (!jobDescription) {
      api.showToast("Please provide the target job description.", "error");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner" style="width:18px;height:18px;"></span> Computing ATS Metrics...`;

      const res = await api.post("/api/analyze", {
        resume_text: resumeText,
        job_description: jobDescription,
        job_title: targetTitle
      });

      if (res.success && res.analysis) {
        renderAnalysisResults(res.analysis);
        api.showToast("Analysis complete!", "success");

        // Smooth scroll to results
        document.getElementById("analysis-results")?.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      api.showToast(err.message || "Analysis failed.", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `🔍 Run NLP ATS Analysis`;
    }
  });
}

function renderAnalysisResults(analysis) {
  const container = document.getElementById("analysis-results");
  if (!container) return;
  container.style.display = "block";

  const scores = analysis.scores;

  // 1. Overall Score & Verdict
  const overallEl = document.getElementById("result-overall-score");
  const verdictEl = document.getElementById("result-verdict");
  const gaugeSvg = document.getElementById("score-meter-circle");

  if (overallEl) overallEl.textContent = `${scores.overall}%`;
  
  if (verdictEl && analysis.summary) {
    verdictEl.textContent = analysis.summary.verdict || "Match Analysis Complete";
    verdictEl.className = "badge " + (
      scores.overall >= 75 ? "badge-offer" :
      scores.overall >= 50 ? "badge-assessment" : "badge-rejected"
    );
  }

  // Update circular SVG gauge stroke-dasharray (circumference ~ 283)
  if (gaugeSvg) {
    const radius = 45;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (scores.overall / 100) * circumference;
    gaugeSvg.style.strokeDashoffset = offset;
    gaugeSvg.style.stroke = scores.overall >= 75 ? "#10b981" : (scores.overall >= 50 ? "#f59e0b" : "#ef4444");
  }

  // 2. Breakdown Progress Bars
  setProgressBar("bar-skill", "val-skill", scores.skill_match);
  setProgressBar("bar-similarity", "val-similarity", scores.semantic_similarity);
  setProgressBar("bar-keyword", "val-keyword", scores.keyword_match);
  setProgressBar("bar-experience", "val-experience", scores.experience_relevance);

  // 3. Matched Skills & Missing Skills (Skill Gaps)
  renderChipList("matched-skills-container", analysis.matching_skills, "chip-success");
  renderChipList("missing-skills-container", analysis.missing_skills, "chip-danger");

  // 4. Keywords
  renderChipList("matched-keywords-container", analysis.matching_keywords, "chip-success");
  renderChipList("missing-keywords-container", analysis.missing_keywords, "chip-danger");

  // 5. Named Entities
  const entities = analysis.entities || {};
  renderChipList("entities-orgs-container", entities.organizations || [], "chip");
  renderChipList("entities-locs-container", entities.locations || [], "chip");
  renderChipList("entities-dates-container", entities.dates_or_periods || [], "chip");

  // 6. Executive Summary & Tailoring Recommendations
  const summary = analysis.summary || {};
  renderBulletList("summary-strengths-list", summary.strengths || []);
  renderBulletList("summary-gaps-list", summary.critical_gaps || []);
  renderBulletList("summary-recommendations-list", summary.actionable_recommendations || []);
}

function setProgressBar(barId, valId, value) {
  const bar = document.getElementById(barId);
  const val = document.getElementById(valId);
  if (bar) bar.style.width = `${Math.min(100, Math.max(0, value))}%`;
  if (val) val.textContent = `${value}%`;
}

function renderChipList(containerId, items, chipClass) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!items || items.length === 0) {
    container.innerHTML = `<span style="font-size:0.85rem; color:var(--gray-500);">None identified</span>`;
    return;
  }

  container.innerHTML = items.map(item => `
    <span class="chip ${chipClass}">${escapeHtml(item)}</span>
  `).join("");
}

function renderBulletList(containerId, items) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!items || items.length === 0) {
    container.innerHTML = `<li>No specific recommendations.</li>`;
    return;
  }

  container.innerHTML = items.map(item => `
    <li style="margin-bottom: 0.5rem; line-height: 1.45;">${escapeHtml(item)}</li>
  `).join("");
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
