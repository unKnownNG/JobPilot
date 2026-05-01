# 🚀 JobPilot: Autonomous AI Job Agent

JobPilot is a local-first, full-stack application designed to automate the painful process of finding and applying for jobs. Built with **FastAPI**, **Next.js**, and powered by **free AI models**, it acts as your personal autonomous recruiter.

![Dashboard Preview](https://via.placeholder.com/1000x500.png?text=JobPilot+Dashboard) *(Replace with actual screenshot)*

## 🌟 Features

*   **Secure Authentication:** Local-first JWT authentication with secure `bcrypt` password hashing.
*   **Premium Dashboard:** A modern, dark-themed Next.js interface featuring glassmorphism and real-time statistics.
*   **Master Resume Management:** Store and easily edit your master resume using a structured JSON format.
*   **The Scout Agent (Job Discovery):**
    *   Automatically fetches remote jobs from public APIs (like Remotive).
    *   Passes job descriptions and your resume to an AI language model (Pollinations API).
    *   Scores the relevance of the job (0-100%) and saves high-matching jobs to your dashboard.
*   **Application Pipeline Tracking:** A visual funnel to track jobs from "Discovered" to "Applied", "Interviewing", and "Offer".

## 🏗️ Architecture

JobPilot is a monorepo separated into two distinct services:

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

---

## 🚀 Getting Started

### Prerequisites
*   [Node.js](https://nodejs.org/) (v18+)
*   [Python](https://www.python.org/) (v3.10+)

### Quick Start (Windows)
We've included a convenient batch script to launch both servers simultaneously:
1. Double-click the `start.bat` file in the root directory.
2. The frontend will be available at `http://localhost:3000`.
3. The backend API docs (Swagger UI) will be available at `http://localhost:8000/docs`.

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv .venv
# Activate venv: .venv\Scripts\activate (Windows) or source .venv/bin/activate (Mac/Linux)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🤖 The AI Agents Roadmap

JobPilot is designed around modular AI agents. Here is the implementation roadmap:

*   [x] **Phase 1: Foundation.** Authentication, Database, CRUD, UI.
*   [x] **Phase 2: Scout Agent.** Scrapes remote jobs, AI scores them against user resume, and flags good matches.
*   [ ] **Phase 3: Tailor Agent.** Looks for user-approved jobs, uses AI to rewrite resume bullets to perfectly match the job description.
*   [ ] **Phase 4: Applier Agent.** Uses browser automation (Playwright) to physically navigate to job portals, fill forms, upload tailored resumes, and submit.
*   [ ] **Phase 5: Sentinel Agent.** Connects to IMAP email to scan for "Interview Request" or "Rejection" emails, automatically updating dashboard statuses.

## 🔒 Privacy & Security

Because JobPilot uses SQLite, **your data never leaves your computer** (with the exception of sending your resume to the AI model for scoring/tailoring). Your passwords are cryptographically hashed using `bcrypt` and are never stored in plaintext.

## 🤝 Contributing
Contributions are welcome as we continue to build out the autonomous agents (Phases 3-5). Feel free to fork the repository and submit pull requests.
