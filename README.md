# JobPilot ✈

An autonomous AI job agent that finds jobs, tailors your resume, and fills out applications — so you don't have to.

Built with **FastAPI**, **Next.js**, and a **Chrome Extension**.

---

## The Agents

| Agent | What it does |
|---|---|
| **Scout** | Scrapes job boards, scores each listing against your resume (0–100), and saves the best matches. |
| **Tailor** | Rewrites your resume bullets to better match a specific job description. |
| **Applier** | Opens job application pages in your browser and auto-fills every form field using your resume and AI. |

> The Chrome Extension powers the Applier — it scans the form on any job page and triggers the fill from the popup.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI (Python), SQLite, SQLAlchemy |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| AI | Pollinations API (free, no key required by default) |
| Extension | Chrome Manifest V3 |

---

## Quickstart

### Option A — Docker (Recommended)

The easiest way to run JobPilot. Docker handles Python, Node.js, and all dependencies automatically — you don't need to install anything else.

#### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — free, available for Windows, Mac, and Linux.
- Make sure Docker Desktop is **open and running** before proceeding (look for the whale icon in your taskbar).

#### Steps

**1. Clone the repository**
```bash
git clone https://github.com/unKnownNG/JobPilot.git
cd JobPilot
```

**2. Set up your environment variables**
```bash
# On Mac/Linux:
cp backend/.env.example backend/.env

# On Windows (PowerShell):
copy backend\.env.example backend\.env
```

Open `backend/.env` in any text editor. The defaults work out of the box for local use — you don't need any API keys to get started. The file looks like this:
```
SECRET_KEY=your-secret-key-here        # Any random string, used for JWT auth
DATABASE_URL=sqlite:///./data/db.sqlite3
LLM_PROVIDER=pollinations               # Free AI, no key needed
```

**3. Build and start everything**
```bash
docker compose up --build
```

> ☕ The first build takes 3–5 minutes — Docker is downloading Python, Node.js, and all packages. Subsequent starts are near-instant because everything is cached.

You'll know it's ready when you see:
```
jobpilot-backend  | INFO:     Application startup complete.
jobpilot-frontend | ✓ Ready in 0ms
```

**4. Open the app**

- 🌐 **Dashboard** → [http://localhost:3000](http://localhost:3000)
- 📡 **API Docs** → [http://localhost:8000/docs](http://localhost:8000/docs)

Create an account on the dashboard, upload your resume, and you're good to go.

**5. Stop the app**
```bash
docker compose down
```

> 💾 Your database and uploaded resumes are stored in `backend/data/` on your local machine — not inside Docker. Stopping or deleting containers will **not** delete your data.

**Other useful commands:**

| Command | What it does |
|---|---|
| `docker compose up -d` | Start in the background (detached mode) |
| `docker compose logs -f` | View live logs from all services |
| `docker compose logs backend` | View backend logs only |
| `docker compose up --build` | Rebuild images after code changes |

---

### Option B — Manual Setup (Development)

Use this if you want to modify the code and see changes live with hot-reload.

#### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js v18+](https://nodejs.org/)
- A Chromium-based browser (Chrome, Edge, or Brave) for the extension

#### Step 1 — Backend (FastAPI)

**1. Navigate to the backend folder**
```bash
cd backend
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows (PowerShell):
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```
You should see `(venv)` appear at the start of your terminal prompt — this means the virtual environment is active.

**3. Install dependencies**
```bash
pip install -r requirements.txt
pip install -e .
```
This installs FastAPI, SQLAlchemy, JobSpy (job scraping), Playwright, PDF parsers, and everything else the backend needs.

**4. Set up environment variables**
```bash
# Windows:
copy .env.example .env

# Mac/Linux:
cp .env.example .env
```
Open `.env` and set a `SECRET_KEY` value (any random string works). The rest of the defaults are fine.

**5. Start the backend server**
```bash
python -m uvicorn app.main:app --reload --port 8000
```
The server starts at [http://localhost:8000](http://localhost:8000). The `--reload` flag means it automatically restarts whenever you save a file.

On first startup, the database tables are created automatically — you'll see SQLAlchemy log output confirming this.

#### Step 2 — Frontend (Next.js)

Open a **new terminal window** (keep the backend running in the first one).

**1. Navigate to the frontend folder**
```bash
cd frontend
```

**2. Install dependencies**
```bash
npm install
```

**3. Start the development server**
```bash
npm run dev
```
The frontend starts at [http://localhost:3000](http://localhost:3000) with hot-reload enabled.

#### Windows Shortcut

Double-click **`start.bat`** in the root folder to launch both the backend and frontend at the same time in separate windows.

---

## Chrome Extension

The extension lives in `/extension` and requires no build step.

**Installation:**

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked** and select the `/extension` folder
4. Pin the **JobPilot ✈** icon to your toolbar

**Usage:**

1. Navigate to any job application page
2. Click the extension icon → **Scan Form Fields**
3. Click **Auto-Fill Form** — the AI fills every field using your resume
4. Review, correct if needed, then submit
5. Click **Log Application** to save it to your dashboard

> The backend must be running on `localhost:8000` for the extension to work. Register and upload your resume on the dashboard first.

**Works on:** LinkedIn Easy Apply, Greenhouse, Lever, Workday, Indeed, and most standard job forms.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Extension can't connect | Make sure the backend is running on port 8000 |
| No form fields found | Scroll down to fully load the form before scanning |
| Session expired | Click Sign In again in the popup |
| Wrong AI answers | Update your resume on the dashboard — the AI needs complete data |
| Extension icon missing | Go to `chrome://extensions/`, click the puzzle piece, and pin JobPilot |

---

## Privacy

Your data stays on your machine. JobPilot uses SQLite (local file), passwords are hashed with `bcrypt`, and the extension only talks to `localhost:8000`. The only data that leaves your computer is the form fields + resume content sent to the AI model for analysis.

---

## Contributing

Fork the repo and submit a pull request — contributions are welcome.
