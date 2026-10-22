# OFFERPATH – JOB APPLICATION INTELLIGENCE PLATFORM

> A full-stack, production-ready career intelligence and job application tracking platform.  
> Designed for college placement preparation, portfolio demonstrations, and intelligent career management.

---

## 🌟 Platform Overview & Core Features

OfferPath combines full-stack web technologies, classical Natural Language Processing (NLP), and Generative AI to guide job seekers from application submission to interview success:

1. **Kanban Application Tracker**: Interactive 6-stage pipeline (`Saved`, `Applied`, `Assessment`, `Interview`, `Offer`, `Rejected`) with HTML5 Drag-and-Drop and responsive status selectors.
2. **Resume Multi-Format Ingestion**: Upload resumes in **PDF** (via `pypdf`/`PyPDF2`), **Word DOCX** (via `python-docx`), or **Plain Text (.txt)** with automated text sanitization.
3. **NLP-Powered ATS Resume Analyzer**:
   - **TF-IDF + Cosine Similarity**: Scikit-Learn vectorization with $n$-gram analysis calculating mathematical document similarity against job descriptions.
   - **Keyword Gap Identification**: Top job description keywords categorized into **Matching Keywords** and **Missing Keywords**.
   - **Skill Gap Taxonomy**: 300+ technical skills categorized into Programming Languages, Frameworks, Cloud, Databases, DevOps, and Soft Skills.
   - **spaCy Named Entity Recognition (NER)**: Extracts organizations, universities, geographic locations, and dates.
4. **Transparent ATS Scoring Engine**: An explainable, deterministic scoring formula breaking down Skill Match, Semantic Similarity, Keyword Match, and Experience Relevance.
5. **Google Gemini AI Interview Prep**: Generates 10 realistic interview questions categorized into **Technical**, **Project Deep-Dive**, **Behavioral**, **Resume-Based**, and **Job-Description-Specific** with interviewer rationales.
6. **Live Analytics & Funnel Charts**: Built with Chart.js displaying real-time stage distributions, conversion velocity, and monthly trendlines.
7. **Secure User Authentication**: Bcrypt/scrypt hashed passwords, JWT Bearer token sessions, and strict per-user data isolation.

---

## 📐 Transparent ATS Scoring Formula

The overall ATS-style compatibility score is computed deterministically:

$$\text{ATS Score} = (0.35 \times \text{Skill Match}) + (0.30 \times \text{Semantic Similarity}) + (0.20 \times \text{Keyword Match}) + (0.15 \times \text{Experience Relevance})$$

### Component Breakdown:
1. **Skill Match (35% Weight)**:
   $$\text{Skill Match} = \frac{\text{Count of Matched Skills}}{\max(\text{Count of Required Skills in JD}, 1)} \times 100\%$$
   Compares technical and domain skills from the job description against the candidate's resume using a comprehensive taxonomy.
2. **TF-IDF Cosine Similarity (30% Weight)**:
   Transforms the resume and job description into $n$-gram TF-IDF vectors using `scikit-learn` and calculates cosine similarity:
   $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
3. **Keyword Match (20% Weight)**:
   Extracts top salient terms and bigrams from the job description using TF-IDF weights, evaluates whole-word matches in the resume, and calculates coverage percentage.
4. **Experience & Role Relevance (15% Weight)**:
   Analyzes alignment of target job title, seniority indicators (Entry, Junior, Mid, Senior, Lead), and degree/education keywords (B.S., M.S., Computer Science, Engineering).

> **Disclaimer**: This is an explainable ATS-style metric designed for feedback and tailoring. Commercial ATS systems use proprietary algorithms.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.11+ / 3.12+, Flask 3.1, RESTful API Blueprints |
| **Database & ORM** | PostgreSQL (Primary) / SQLite (Zero-setup option), SQLAlchemy, Flask-SQLAlchemy |
| **NLP & Machine Learning** | spaCy (`en_core_web_sm`), scikit-learn, NumPy, SciPy |
| **Document Processing** | `pypdf`, `python-docx` |
| **Generative AI** | Google Gemini API (`google-genai` SDK and REST endpoint) |
| **Security & Auth** | PyJWT, Werkzeug scrypt password hashing, Flask-CORS |
| **Frontend** | Semantic HTML5, Modern CSS, Vanilla JavaScript, Chart.js |
| **Testing** | `pytest` test suite |

---

## 🚀 Step-by-Step Beginner Setup Guide (Windows / VS Code)

Follow this complete step-by-step tutorial to run OfferPath on Windows PowerShell or Command Prompt.

```
DOWNLOAD ZIP  ➜  EXTRACT ZIP  ➜  OPEN IN VS CODE  ➜  CREATE VENV  ➜  INSTALL DEPS  ➜  RUN
```

---

### Step 1: Extract the ZIP and Open in VS Code

1. Download `OfferPath.zip`.
2. Right-click `OfferPath.zip` and select **Extract All...** to your desired folder (e.g. `C:\Projects\OfferPath`).
3. Open **Visual Studio Code**.
4. In VS Code, click **File ➜ Open Folder...** and select the extracted `OfferPath` root folder.

---

### Step 2: Open Terminal in VS Code

In VS Code, press `Ctrl + ~` (or go to **Terminal ➜ New Terminal** in the top menu). Ensure your terminal is in the `OfferPath` directory:

```powershell
pwd
# Expected output ends with: ...\OfferPath
```

---

### Step 3: Create and Activate Virtual Environment

Create an isolated Python virtual environment:

#### In Windows PowerShell:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

*(If PowerShell displays an `Execution_Policies` warning, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and run `venv\Scripts\Activate.ps1` again).*

#### Or in Windows Command Prompt (CMD):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

Once activated, your prompt will show `(venv)` at the beginning.

---

### Step 4: Install Dependencies

Navigate to the `backend` folder and install all required libraries:

```powershell
cd backend
pip install -r requirements.txt
```

---

### Step 5: Install spaCy NLP Model

Download the pre-trained English NLP pipeline for Named Entity Recognition:

```powershell
python -m spacy download en_core_web_sm
```

*(Note: OfferPath also includes a graceful regex fallback if the model is not installed, but downloading it enables full NER extraction).*

---

### Step 6: Configure Environment Variables (`.env`)

In the `backend` folder (or root folder), copy `.env.example` to `.env`:

```powershell
# PowerShell:
Copy-Item .env.example .env

# Or CMD:
copy .env.example .env
```

Now open `.env` in VS Code and review the configuration:

```ini
# Flask Application Settings
FLASK_ENV=development
SECRET_KEY=offerpath-super-secret-key-change-in-production-2026

# Database Configuration (PostgreSQL by default)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/offerpath

# Optional Zero-Setup Local Testing without PostgreSQL:
# If you don't have PostgreSQL installed yet, simply uncomment the line below:
# DATABASE_URL=sqlite:///offerpath.db

# Google Gemini API Key (Get free key: https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

JWT_SECRET_KEY=offerpath-jwt-secret-key-at-least-32-bytes-long!
JWT_EXPIRATION_HOURS=72
```

---

### Step 7: Database Setup (PostgreSQL or SQLite)

#### Option A: Using PostgreSQL (Recommended)
1. Install PostgreSQL from [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/) (or use pgAdmin).
2. Open **psql** or pgAdmin Query Tool:
   ```sql
   CREATE DATABASE offerpath;
   ```
3. Update `DATABASE_URL` in `.env` with your PostgreSQL username and password:
   ```ini
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/offerpath
   ```

#### Option B: Zero-Setup SQLite (Instant Test)
If you want to test immediately without configuring PostgreSQL, set in `.env`:
```ini
DATABASE_URL=sqlite:///offerpath.db
```

---

### Step 8: Seed Sample Data (Applications, Resume & Questions)

Run the seeding script to create database tables and populate realistic sample applications across all 6 stages:

```powershell
python seed.py
```

**Output will confirm:**
```
=================================================================
 OFFERPATH DATABASE SEEDING COMPLETED SUCCESSFULLY!
=================================================================
 You can now test the platform using the pre-seeded account:
   Email:    demo@offerpath.com
   Username: demouser
   Password: password123
=================================================================
```

---

### Step 9: Start the Application

Start the Flask application server:

```powershell
python run.py
```

You will see:
```
=================================================================
 OFFERPATH – JOB APPLICATION INTELLIGENCE PLATFORM
=================================================================
 * Server running on: http://127.0.0.1:5000/
 * API Health Check:  http://127.0.0.1:5000/api/health
 * Environment:       development
=================================================================
```

---

### Step 10: Open in Your Browser

Open your browser (Chrome, Edge, Firefox) and navigate to:

👉 **[http://localhost:5000](http://localhost:5000)**

1. Click **Auto-Fill** to use the pre-seeded demo credentials (`demo@offerpath.com` / `password123`) or register a new account.
2. Explore your **Kanban Dashboard** with 6 status columns. Drag and drop cards to change stages!
3. Go to **Applications** to search, filter, add, or edit job postings.
4. Go to **Resume Analysis** to upload a PDF/DOCX resume and test the ATS Match engine.
5. Go to **AI Interview Prep** to generate questions tailored to the job description and your resume!

---

## 🧪 Running Automated Tests

OfferPath includes a complete test suite covering registration, authentication, application CRUD, user isolation, TF-IDF cosine similarity, skill gap detection, and ATS scoring.

Run all tests in your activated terminal inside the `backend` folder:

```powershell
pytest -v
```

All 18 tests will execute and pass:
```
tests/test_applications.py::test_create_application PASSED
tests/test_applications.py::test_get_applications_list PASSED
tests/test_applications.py::test_filter_applications_by_status PASSED
tests/test_applications.py::test_patch_application_status PASSED
tests/test_applications.py::test_delete_application PASSED
tests/test_applications.py::test_user_data_isolation PASSED
tests/test_auth.py::test_register_success PASSED
tests/test_auth.py::test_register_duplicate_username PASSED
tests/test_auth.py::test_register_invalid_email PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_invalid_password PASSED
tests/test_auth.py::test_get_current_user_profile PASSED
tests/test_auth.py::test_unauthenticated_request_fails PASSED
tests/test_nlp_analysis.py::test_skill_extraction PASSED
tests/test_nlp_analysis.py::test_skill_gap_analysis PASSED
tests/test_nlp_analysis.py::test_cosine_similarity PASSED
tests/test_nlp_analysis.py::test_analyze_resume_against_job_full PASSED
tests/test_nlp_analysis.py::test_analyze_api_endpoint PASSED

======================== 18 passed ========================
```

---

## 🔑 Google Gemini API Setup (AI Interview Prep)

OfferPath uses Google Gemini API to generate structured technical, architectural, behavioral, and resume-based questions with interviewer rationales.

1. Obtain a **free** Gemini API key at: **[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**.
2. Open your `backend/.env` file.
3. Replace the placeholder with your key:
   ```ini
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   ```
4. Restart the backend server (`python run.py`).

*(Note: If no API key is provided, the application fails gracefully with an informative banner explaining how to configure the key, without crashing or mocking fake responses).*

---

## 📂 Project Directory Structure

```
OfferPath/
├── backend/
│   ├── app/
│   │   ├── __init__.py            # Flask app factory, CORS, static routes, error handlers
│   │   ├── models/
│   │   │   ├── __init__.py        # SQLAlchemy instance and model exports
│   │   │   ├── user.py            # User account & password hashing
│   │   │   ├── application.py     # 6-stage application tracking
│   │   │   ├── resume.py          # Uploaded resume metadata & parsed text
│   │   │   ├── analysis.py        # ATS scores & NLP entity history
│   │   │   └── interview_question.py # AI interview questions
│   │   ├── routes/
│   │   │   ├── auth.py            # /api/auth (Register, Login, Me)
│   │   │   ├── applications.py    # /api/applications (CRUD, filter, status patch)
│   │   │   ├── resume.py          # /api/resume (Upload PDF/DOCX/TXT)
│   │   │   ├── analysis.py        # /api/analyze (NLP ATS scoring)
│   │   │   ├── interview.py       # /api/interview (Gemini AI generator)
│   │   │   └── analytics.py       # /api/analytics (Chart.js metrics)
│   │   ├── services/
│   │   │   ├── text_extractor.py  # PDF, DOCX, and TXT parsing
│   │   │   ├── skill_extractor.py # 300+ skill taxonomy & gap analysis
│   │   │   ├── nlp_analyzer.py    # TF-IDF, Cosine Similarity, spaCy NER
│   │   │   └── gemini_service.py  # Google Gemini structured API integration
│   │   └── utils/
│   │       ├── auth_helpers.py    # JWT generator & @token_required decorator
│   │       └── validators.py      # Input validation & file security
│   ├── tests/
│   │   ├── conftest.py            # Pytest fixtures & isolated test DB
│   │   ├── test_auth.py           # Auth & JWT tests
│   │   ├── test_applications.py   # Applications CRUD & isolation tests
│   │   └── test_nlp_analysis.py   # NLP, TF-IDF, and ATS score tests
│   ├── config.py                  # Environment config classes
│   ├── run.py                     # Server executable entrypoint
│   ├── seed.py                    # Database seeder with demo account
│   └── requirements.txt           # Pinned production dependencies
│
├── frontend/
│   ├── index.html                 # Landing & Login portal
│   ├── register.html              # Account registration
│   ├── dashboard.html             # Kanban board & Chart.js analytics
│   ├── applications.html          # Application tracking table & filters
│   ├── resume-analysis.html       # ATS score gauge & skill gap visualizer
│   ├── interview.html             # Gemini AI interview prep studio
│   ├── css/
│   │   ├── style.css              # Modern global stylesheet
│   │   └── kanban.css             # Kanban drag-and-drop styles
│   └── js/
│       ├── api.js                 # Centralized fetch wrapper & JWT headers
│       ├── auth.js                # Auth controller & guards
│       ├── dashboard.js           # Kanban drag-and-drop & Chart.js setup
│       ├── applications.js        # Table CRUD & modal controller
│       ├── analysis.js            # Resume upload & ATS visualizer
│       └── interview.js           # Gemini AI questions controller
│
├── sample_data/
│   ├── sample_resumes/            # Sample resumes for testing
│   ├── sample_job_descriptions/   # Sample JDs for testing
│   └── sample_seed_data.json      # Structured reference data
│
├── uploads/                       # Safe resume upload storage
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git ignore rules
├── RUN_INSTRUCTIONS.txt           # Quick-start cheat sheet
└── README.md                      # Comprehensive guide
```

---

## ❓ Troubleshooting & FAQs

### 1. `psycopg2` / PostgreSQL Connection Error
- **Cause**: PostgreSQL is not running or the password in `.env` is incorrect.
- **Fix**: Check that the PostgreSQL service is running and that `DATABASE_URL` matches your local credentials. Alternatively, set `DATABASE_URL=sqlite:///offerpath.db` in `.env` for zero-setup instant testing.

### 2. `Execution of scripts is disabled on this system` in PowerShell
- **Fix**: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in PowerShell, then activate `venv\Scripts\Activate.ps1`.

### 3. `Can't find model 'en_core_web_sm'`
- **Fix**: Run `python -m spacy download en_core_web_sm`. Even without this command, OfferPath includes an automated fallback entity extractor that prevents crashes.

### 4. Gemini API Error
- **Fix**: Ensure your `GEMINI_API_KEY` is pasted into `backend/.env` without quotes, and restart `python run.py`. Verify that your key is active in [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## 📄 License
This project is open-source and intended for academic, portfolio, and placement project use.
