# JobPilot — How to Use

This guide walks you through using JobPilot from first login to your first application.

---

## 1. Create an Account

Open [http://localhost:3000](http://localhost:3000) and register with an email and password.  
All data stays on your machine — nothing is sent to any server except the job text/form fields sent to the AI for analysis.

---

## 2. Upload Your Resume

Go to the **Resume** tab.

- **Upload (recommended):** Drag and drop your PDF, DOCX, or TXT file onto the upload zone, or click it to browse. The AI will parse it automatically (~20 seconds).
- **Manual entry:** Click **Edit Manually** to fill in your details directly in the form (name, title, skills, experience, education, projects).

Your resume is the single source of truth for everything — the Scout uses it to score jobs, the Tailor uses it to rewrite bullets, and the Applier uses it to fill forms. **Keep it accurate and complete.**

> You can re-upload or edit your resume at any time. Only the most recent version is used.

---

## 3. Run the Agents

Go to the **Agents** tab. Run them in this order:

---

### 🔍 Scout Agent

**What it does:** Scrapes LinkedIn, Indeed, Naukri, Adzuna, Remotive, and Himalayas for job listings, then uses AI to score each one (0–100) against your resume. Only jobs above your minimum score are saved.

**Settings:**
| Setting | What it controls |
|---|---|
| Min relevance score | Only jobs scoring above this are saved. Default: 45%. Lower it if you get 0 results. |
| Search query | Keyword to search for. Leave blank to auto-detect from your resume title. |
| Max jobs to fetch | How many listings to pull per source. Default: 50. |

**Click "Run Scout Agent"** and wait. It typically takes 1–3 minutes.

When done, you'll see a summary: how many jobs were fetched, scored, and saved. If it shows **0 saved**:
- Lower the **Min relevance score** slider.
- Use a broader **Search query** (e.g. `developer` instead of `senior React developer`).
- Increase **Max jobs to fetch**.

---

### ✍️ Tailor Agent

**What it does:** Takes every job you've **Approved** (in the Jobs tab) and rewrites your resume bullets to better match each job description. Reorders your skills so the most relevant ones appear first. Creates an **Application** entry for each job with a tailored resume ready to send.

**Before running:** Go to the **Jobs** tab and approve at least one job.

**Click "Run Tailor Agent"** — it takes ~10–30 seconds per job.

---

### ✈️ Applier Agent (Chrome Extension)

**What it does:** Fills out job application forms in your browser using your resume data and AI — without any bots or headless browsers. Since it runs inside your own logged-in Chrome session, it bypasses CAPTCHAs and login walls automatically.

This agent works differently — it runs from the **Chrome Extension**, not the dashboard.

See [Section 5](#5-using-the-chrome-extension) below.

---

## 4. Review Jobs

Go to the **Jobs** tab after the Scout finishes.

- Each job card shows the **title**, **company**, **location**, and an AI **relevance score** (%).
- Filter by status: **All / Discovered / Approved / Rejected / Applied**.
- For each discovered job: click **Approve** to send it to the Tailor, or **Reject** to skip it.
- Click **Open** to view the original listing before deciding.

You can also **Import a job from URL** — paste any job board link and the AI will extract and score it automatically.

---

## 5. Using the Chrome Extension

**Install once:**
1. Open `chrome://extensions/` in Chrome.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked** → select the `/extension` folder from the project.
4. Pin the **JobPilot ✈** icon to your toolbar.

**To fill an application:**
1. Open any job application page in Chrome.
2. Click the **JobPilot ✈** extension icon.
3. Click **Scan Form Fields** — it detects every input on the page.
4. Click **Auto-Fill Form** — the AI maps your resume data to each field and fills them instantly.
5. Review the filled values, correct anything if needed, then submit manually.
6. Click **Log Application** in the popup to save it to your Applications tab.

> The backend must be running on `localhost:8000` for the extension to work.

---

## 6. Track Applications

Go to the **Applications** tab to see all your tailored resumes and logged applications.

Each application shows:
- The job it was created for.
- The tailored resume the Tailor generated.
- The current status: `resume_ready` → `applied` → `under_review` → `interview_scheduled` → `offer_received`.

Update the status manually as you hear back from companies.

---

## 7. Overview Dashboard

The **Overview** tab gives you a bird's-eye view:
- Total jobs discovered, applications sent, interviews, and offers.
- An **Application Funnel** showing how many applications are at each stage.
- **Jobs by Status** breakdown.
- Quick access to the last Scout and Tailor runs.
- Recent jobs list.

---

## Typical Workflow (First Time)

```
1. Upload resume          → Resume tab
2. Run Scout Agent        → Agents tab
3. Review & approve jobs  → Jobs tab
4. Run Tailor Agent       → Agents tab
5. Open job pages in      → Chrome Extension
   Chrome & auto-fill
6. Track progress         → Applications + Overview tabs
```

Repeat steps 2–6 regularly (e.g. weekly) to keep finding new jobs.
