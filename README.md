# 🚀 JobPilot: Autonomous AI Job Agent

JobPilot is a local-first, full-stack application designed to automate the painful process of finding and applying for jobs. Built with **FastAPI**, **Next.js**, and powered by **free AI models**, it acts as your personal autonomous recruiter.

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

## 🚀 Getting Started & Installation

### Prerequisites
*   [Node.js](https://nodejs.org/) (v18+)
*   [Python](https://www.python.org/) (v3.10+)

### Step 1: Backend Setup (Python)

Your backend is built with FastAPI and uses Playwright for browser automation.

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
   JobPilot uses `pyproject.toml` to manage dependencies. You will also need to explicitly install `playwright` for the browser agents:
   ```bash
   pip install -e .
   pip install playwright
   ```
   *Note: If you run into issues with the above, install the core packages manually: `pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite alembic "python-jose[cryptography]" "passlib[bcrypt]" bcrypt pydantic pydantic-settings httpx python-multipart python-dotenv playwright`*
4. **Install Playwright Browsers:**
   Playwright requires a headless browser to automate job applications.
   ```bash
   playwright install chromium
   ```
5. **Setup Environment Variables:**
   Duplicate the `.env.example` file and rename it to `.env`. Fill in any necessary keys (like your `POLLINATIONS_API_KEY`, if you have one).
6. **Run Database Migrations:**
   Ensure your SQLite database is fully set up:
   ```bash
   alembic upgrade head
   ```

### Step 2: Frontend Setup (Next.js)

1. **Navigate to the frontend directory:**
   ```bash
   cd ../frontend
   ```
2. **Install Node Packages:**
   ```bash
   npm install
   ```

### Step 3: Running the Project Locally

We've included a convenient batch script to launch both servers simultaneously on Windows!

1. **Navigate to the root folder:**
   ```bash
   cd ..
   ```
2. **Run the start script:**
   Double-click the **`start.bat`** file in your File Explorer, OR run it from your terminal:
   ```bash
   .\start.bat
   ```

This will automatically open two terminal windows (one for the backend on `http://localhost:8000` and one for the frontend).
Open your browser and navigate to **[http://localhost:3000](http://localhost:3000)** to view the JobPilot application!

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
