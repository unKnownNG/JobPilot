# 🚀 JobPilot: Autonomous AI Job Agent

JobPilot is a local-first, full-stack application designed to automate the painful process of finding and applying for jobs. Built with **FastAPI**, **Next.js**, and a **Chrome Extension**, it acts as your personal autonomous recruiter — sitting right inside your browser.

## 🌟 Features

*   **Secure Authentication:** Local-first JWT authentication with secure `bcrypt` password hashing.
*   **Premium Dashboard:** A modern, dark-themed Next.js interface featuring glassmorphism and real-time statistics.
*   **Master Resume Management:** Store and easily edit your master resume using a structured JSON format.
*   **The Scout Agent (Job Discovery):**
    *   Automatically fetches remote jobs from public APIs (like Remotive).
    *   Passes job descriptions and your resume to an AI language model (Pollinations API).
    *   Scores the relevance of the job (0-100%) and saves high-matching jobs to your dashboard.
*   **Application Pipeline Tracking:** A visual funnel to track jobs from "Discovered" to "Applied", "Interviewing", and "Offer".
*   **AI Form Filler Chrome Extension:** A browser extension that reads any job application form, sends the fields to your backend AI, and auto-fills answers using your resume data.

## 🏗️ Architecture

JobPilot is a monorepo with three distinct parts:

### 1. Backend (`/backend`)
*   **Framework:** FastAPI (Python)
*   **Database:** SQLite via asynchronous SQLAlchemy (`aiosqlite`)
*   **AI Integration:** `LLMProvider` using the free Pollinations AI text generation API.
*   **Design Pattern:** Modular architecture (`/api` routers, `/models` DB tables, `/schemas` Pydantic validation, `/agents` AI logic).

### 2. Frontend (`/frontend`)
*   **Framework:** Next.js 14+ (App Router)
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS v4 with custom variables for a sleek, dark UI.
*   **State Management:** React Context (`auth-context.tsx`) for global user sessions.

### 3. Chrome Extension (`/extension`)
*   **Type:** Manifest V3 Chrome Extension
*   **Role:** Runs inside the browser as a "Copilot" — scans job forms, talks to your local backend for AI analysis, and fills in answers automatically.
*   **Key Files:**
    | File | Purpose |
    |---|---|
    | `manifest.json` | Extension config — permissions, icons, entry points |
    | `popup.html` / `popup.css` | The extension's UI panel |
    | `popup.js` | Main logic: login, scan, fill, and log |
    | `content.js` | Injected into every page for visual feedback |
    | `background.js` | Service worker for auth state and API health checks |

---

## 🚀 Getting Started & Installation

### Prerequisites
*   [Node.js](https://nodejs.org/) (v18+)
*   [Python](https://www.python.org/) (v3.10+)
*   A Chromium-based browser (Chrome, Edge, or Brave)

### Step 1: Backend Setup (Python)

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```
2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. **Install Python Packages:**
   JobPilot includes a `requirements.txt` file and a `pyproject.toml` with all necessary dependencies (including JobSpy, Playwright, PDF parsers, and web frameworks).
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
4. **Setup Environment Variables:**
   Duplicate `.env.example`, rename it to `.env`, and fill in any keys.
5. **Run the Server:**
   The database tables are created automatically on first startup:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

### Step 2: Frontend Setup (Next.js)

1. **Navigate to the frontend directory and install packages:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Step 3: Quick Start (Windows)

Double-click **`start.bat`** in the root folder to launch both the backend and frontend simultaneously. Then open **[http://localhost:3000](http://localhost:3000)** to access the dashboard.

---

## 🧩 Chrome Extension — Installation & Usage Guide

The extension is the core of the Applier workflow. It lives in the `/extension` folder and requires **no build step** — you load it directly into Chrome.

> ⚠️ **The backend must be running** on `http://localhost:8000` for the extension to work. Start it first with `start.bat` or manually.

---

### 📦 Installing the Extension

1. **Open Chrome Extensions Manager**
   Navigate to `chrome://extensions/` in your browser's address bar.

2. **Enable Developer Mode**
   Toggle the **"Developer mode"** switch in the **top-right corner** of the page.

3. **Load the Unpacked Extension**
   Click **"Load unpacked"** (top-left) and select the `/extension` folder from your JobPilot project:
   ```
   d:\Projects\Job Agent\extension
   ```

4. **Confirm Installation**
   You should now see the **JobPilot ✈** card appear in your extensions list. The extension icon will appear in your Chrome toolbar (you may need to click the puzzle-piece icon and pin it).

---

### 🔑 Signing In

The extension shares the same login credentials as your JobPilot web dashboard.

1. Click the **JobPilot ✈** icon in your Chrome toolbar to open the popup.
2. Enter your **Email** and **Password** (the same account you use on the dashboard at `http://localhost:3000`).
3. Click **Sign In**. Your session token is saved securely in `chrome.storage.local`, so you only need to log in once.

> 💡 If you don't have an account yet, register one on the dashboard first at **[http://localhost:3000](http://localhost:3000)** and also upload your resume there — the AI needs it to generate answers.

---

### ⚡ Using the Extension on a Job Application

This is the core 3-step workflow:

#### Step 1 — Navigate to a Job Application Page
Open any job application form. The extension works on any website with form fields, including:
*   **LinkedIn Easy Apply** (linkedin.com)
*   **Greenhouse** (boards.greenhouse.io)
*   **Lever** (jobs.lever.co)
*   **Workday** (myworkdayjobs.com)
*   **Indeed** (indeed.com/apply)
*   Any custom careers page with standard HTML form inputs

#### Step 2 — Scan the Form
1. Click the **JobPilot ✈** icon to open the popup.
2. The popup will display the **current page title and URL** at the top.
3. Click **"🔍 Scan Form Fields"**.
4. The extension will scan all visible `<input>`, `<select>`, and `<textarea>` elements on the page and show you a count and preview of the fields it found (e.g., "First Name", "Email", "LinkedIn URL").

#### Step 3 — Auto-Fill with AI
1. After a successful scan, the **"✏️ Auto-Fill Form"** button becomes active.
2. Click it. The popup will show **"AI is thinking..."** while it sends the field list to your backend.
3. The backend AI analyzes each field label against your stored resume and generates the best answer.
4. Fields are filled automatically in the browser. **Filled fields briefly flash green** so you can see what was changed.
5. A summary card appears in the popup showing each filled field and its confidence level (🟢 high / 🟡 medium / 🔴 low).

#### Step 4 — Review & Submit
*   **Always review the filled fields** before submitting — the AI is very good but not perfect.
*   Make any manual corrections if needed.
*   Submit the application yourself.

#### Step 5 — Log the Application (Optional)
1. Once you've submitted (or are happy with the fill), click **"✅ Log Application"** in the popup.
2. This saves the job URL, company name, and filled-field summary to your JobPilot dashboard under the **"Applied"** pipeline stage.
3. You can then track interviews, rejections, and offers from the dashboard.

---

### 🔧 Extension Architecture (How it Works Internally)

```
Browser Tab (Job Form Page)
        │
        │  chrome.scripting.executeScript()
        ▼
   content.js / scanFormFields()      ← reads DOM, returns field list
        │
        │  field list (JSON)
        ▼
   popup.js                           ← sends to backend via fetch()
        │
        │  POST /api/agents/applier/analyze-form
        ▼
   FastAPI Backend                    ← LLM matches fields to resume data
        │
        │  field_mappings (JSON)
        ▼
   popup.js → fillFormFields()        ← injected into tab, fills values
        │
        │  POST /api/agents/applier/log
        ▼
   Dashboard (Applied pipeline)
```

---

### 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| **"API error" or extension can't connect** | Make sure the backend is running: `python -m uvicorn app.main:app --port 8000` |
| **"No form fields found"** | The page may use a non-standard form (e.g., custom divs). Try scrolling down to load the form fully before scanning. |
| **"Session expired"** | Click **Sign In** again in the popup. |
| **Extension icon doesn't appear** | Go to `chrome://extensions/`, click the puzzle-piece icon in the toolbar, and **pin** JobPilot. |
| **After updating extension files** | Go to `chrome://extensions/` and click the **🔄 refresh icon** on the JobPilot card to reload the latest code. |
| **AI fills fields with wrong data** | Your resume may be incomplete. Update it on the dashboard at `http://localhost:3000/resume`. |

---

## 🤖 The AI Agents Roadmap

*   [x] **Phase 1: Foundation.** Authentication, Database, CRUD, UI.
*   [x] **Phase 2: Scout Agent.** Scrapes remote jobs, AI scores them against your resume.
*   [x] **Phase 3: Applier Extension.** Chrome Extension that scans, AI-fills, and logs job applications.
*   [ ] **Phase 4: Tailor Agent.** AI rewrites resume bullets to match the specific job description.
*   [ ] **Phase 5: Sentinel Agent.** Scans your inbox for interview requests and rejections, auto-updates the dashboard.

## 🔒 Privacy & Security

Because JobPilot uses SQLite, **your data never leaves your computer** (with the exception of sending field + resume data to the AI model for analysis). Your passwords are cryptographically hashed using `bcrypt` and are never stored in plaintext. The extension only communicates with `http://localhost:8000` — your own machine.

## 🤝 Contributing
Contributions are welcome! Feel free to fork the repository and submit pull requests.
