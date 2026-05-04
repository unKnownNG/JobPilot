# =============================================================================
# agents/scout.py — Scout Agent v6 (India-First Multi-Source)
# =============================================================================
# Sources (run concurrently):
#   1. JobSpy      — LinkedIn + Indeed India + Naukri + Glassdoor
#   2. Naukri API  — Hits Naukri's internal JSON endpoint directly (no key)
#   3. Adzuna API  — Official REST API, India coverage, salary data (free key)
#   4. Remotive    — Remote-only jobs, no key needed (kept as bonus)
#
# Key fixes over v5:
#   - country_indeed="india" (was "usa" — root cause of US results)
#   - Naukri added to JobSpy site_name list
#   - Custom Naukri scraper for richer/more reliable India data
#   - Adzuna India source added
#   - All sources run concurrently via asyncio.gather
#   - Location defaults to "India" when resume location is missing
# =============================================================================

import re
import asyncio
import httpx
from typing import Optional
from html import unescape
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.llm import llm_provider
from app.models.job_posting import JobPosting
from app.models.resume import MasterResume
from app.models.agent_run import AgentRun
from app.config import settings


_executor = ThreadPoolExecutor(max_workers=4)


# ─── Filter: Title Blocklist ─────────────────────────────────────────────────

TITLE_BLOCKLIST = {
    "teacher", "teaching", "instructor", "professor", "tutor", "lecturer",
    "nurse", "nursing", "physician", "therapist", "dentist", "pharmacist",
    "sales manager", "sales representative", "sales associate", "sales executive",
    "marketing manager", "marketing coordinator", "social media manager",
    "recruiter", "talent acquisition", "hr manager", "hr coordinator",
    "accountant", "bookkeeper", "financial advisor", "loan officer",
    "cashier", "receptionist", "office manager", "administrative assistant",
    "driver", "warehouse", "forklift", "janitor", "custodian",
    "cook", "chef", "barista", "waiter", "bartender",
    "real estate", "property manager", "insurance agent",
    "paralegal", "legal assistant", "attorney",
    "curriculum", "counselor", "principal",
}

TECH_TITLE_KEYWORDS = {
    "engineer", "developer", "programmer", "architect", "devops", "sre",
    "software", "backend", "frontend", "fullstack", "full-stack", "full stack",
    "data scientist", "data analyst", "data engineer", "machine learning", "ml ",
    "ai ", "artificial intelligence", "deep learning", "nlp",
    "cloud", "infrastructure", "platform", "swe", "sdet",
    "qa ", "quality assurance", "test engineer", "automation",
    "security", "cybersecurity", "infosec", "penetration",
    "database", "dba", "system admin", "sysadmin", "linux",
    "mobile", "ios ", "android", "flutter", "react native",
    "web developer", "ui developer", "ux engineer",
    "technical lead", "tech lead", "cto", "vp engineering",
    "solutions architect", "technical", "computing",
}


def is_tech_job(title: str) -> bool:
    t = title.lower()
    for blocked in TITLE_BLOCKLIST:
        if blocked in t:
            return False
    for kw in TECH_TITLE_KEYWORDS:
        if kw in t:
            return True
    return True  # Ambiguous — let LLM decide


# ─── Filter: Skills Overlap ──────────────────────────────────────────────────

def skills_overlap_score(job_desc: str, user_skills: list[str]) -> int:
    if not job_desc or not user_skills:
        return 0
    desc_lower = job_desc.lower()
    return sum(1 for skill in user_skills if skill.lower() in desc_lower)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1500]


def resolve_location(user_location: str) -> str:
    """
    Always return a usable India location.
    If the resume has a specific city, use it. Otherwise fall back to India.
    """
    if not user_location or user_location.strip() == "":
        return "India"
    # If it already mentions India or a known Indian city, return as-is
    india_signals = ["india", "bangalore", "bengaluru", "mumbai", "delhi",
                     "hyderabad", "chennai", "pune", "noida", "gurgaon",
                     "kolkata", "ahmedabad", "coimbatore", "kochi"]
    if any(sig in user_location.lower() for sig in india_signals):
        return user_location
    # Otherwise append India (e.g. resume just says "Chennai")
    return f"{user_location}, India"


def location_bonus(job_location: str, user_location: str) -> int:
    if not user_location or not job_location:
        return 5
    jl = job_location.lower()
    ul = user_location.lower()
    if any(k in jl for k in ["anywhere", "worldwide", "global", "remote"]):
        return 10
    user_tokens = [t.strip() for t in re.split(r"[,\s]+", ul) if len(t.strip()) > 2]
    for token in user_tokens:
        if token in jl:
            return 15
    # Partial India match still gets a small bonus
    if "india" in jl:
        return 5
    return 0


def build_search_queries(resume_data: dict) -> list[str]:
    """Generate multiple targeted search queries from the resume."""
    title = resume_data.get("title", "")
    skills = resume_data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    queries = []
    if title and len(title.split()) >= 2:
        queries.append(title)

    tech_skills = [s for s in skills if len(s) > 1][:6]
    for skill in tech_skills[:3]:
        queries.append(f"{skill} developer")

    if title and len(title.split()) == 1:
        for skill in tech_skills[:2]:
            queries.append(f"{skill} {title}")

    seen = set()
    unique = []
    for q in queries:
        ql = q.lower()
        if ql not in seen:
            seen.add(ql)
            unique.append(q)

    return unique[:4]


# ─── Source 1: JobSpy (LinkedIn + Indeed India + Naukri + Glassdoor) ─────────

def _scrape_jobspy(
    search_term: str,
    location: str = "India",
    results_wanted: int = 20,
    hours_old: int = 72,
) -> list[dict]:
    """
    Synchronous JobSpy scraper — runs in thread pool.

    KEY FIXES:
    - country_indeed="india" → hits indeed.co.in instead of indeed.com
    - "naukri" added to site_name
    - location defaults to "India"
    """
    from jobspy import scrape_jobs

    try:
        df = scrape_jobs(
            site_name=["indeed", "linkedin", "naukri", "glassdoor"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            is_remote=False,
            country_indeed="india",          # ← CRITICAL FIX (was "usa")
            description_format="markdown",
            linkedin_fetch_description=False, # Set True for richer data (slower)
            verbose=0,
        )

        if df is None or df.empty:
            return []

        jobs = []
        for _, row in df.iterrows():
            url = str(row.get("job_url", "") or row.get("job_url_direct", ""))
            if not url or url == "nan":
                continue

            title = str(row.get("title", ""))
            company = str(row.get("company", ""))
            if title == "nan" or not title or company == "nan" or not company:
                continue

            loc = str(row.get("location", "") or "")
            desc = str(row.get("description", "") or "")
            site = str(row.get("site", "unknown") or "unknown")

            if loc == "nan": loc = ""
            if desc == "nan": desc = ""
            if site == "nan": site = "unknown"

            def safe_float(val):
                try:
                    return float(val) if val and str(val) != "nan" else None
                except (ValueError, TypeError):
                    return None

            jobs.append({
                "title":       title,
                "company":     company,
                "url":         url,
                "location":    loc,
                "description": strip_html(desc),
                "source":      site,
                "work_type":   "remote" if row.get("is_remote", False) else "onsite",
                "salary_min":  safe_float(row.get("min_amount")),
                "salary_max":  safe_float(row.get("max_amount")),
                # Naukri-specific fields (populated when source=naukri)
                "skills":      row.get("skills", []) if isinstance(row.get("skills"), list) else [],
                "tags":        [],
            })

        print(f"[JOBSPY] '{search_term}' in '{location}' → {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"[JOBSPY] Error for '{search_term}': {e}")
        return []


async def fetch_jobspy(search_term: str, location: str = "India", results_wanted: int = 20) -> list[dict]:
    """Async wrapper for JobSpy."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _scrape_jobspy, search_term, location, results_wanted, 72
    )


# ─── Source 2: Naukri Internal API (no key needed) ───────────────────────────

async def fetch_naukri(
    keyword: str,
    location: str = "India",
    experience: int = 0,
    results: int = 20,
) -> list[dict]:
    """
    Hits Naukri's internal search JSON endpoint — the same one their
    website frontend calls. No API key required.

    Falls back gracefully if Naukri updates their endpoint.
    """
    # Normalize location for Naukri (strip ", India" suffix if present)
    naukri_loc = location.replace(", India", "").replace(",India", "").strip()
    if naukri_loc.lower() == "india":
        naukri_loc = ""  # Empty = all India

    headers = {
        "User-Agent":   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept":       "application/json, text/plain, */*",
        "Referer":      "https://www.naukri.com/",
        "appid":        "109",
        "systemid":     "Naukri",
        "gid":          "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
    }

    params = {
        "noOfResults":  results,
        "urlType":      "search_by_keyword",
        "searchType":   "adv",
        "keyword":      keyword,
        "k":            keyword,
        "seoKey":       keyword.lower().replace(" ", "-") + "-jobs",
        "src":          "jobsearchDesk",
        "latLong":      "",
    }

    if naukri_loc:
        params["location"] = naukri_loc
        params["l"] = naukri_loc

    if experience > 0:
        params["experience"] = experience

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://www.naukri.com/jobapi/v3/search",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        jobs = []
        for item in data.get("jobDetails", []):
            job_url = f"https://www.naukri.com{item.get('jdURL', '')}"

            # Parse placeholders (location, salary are in here)
            placeholders = item.get("placeholders", [])
            job_loc = ""
            salary_str = ""
            for ph in placeholders:
                label = ph.get("label", "")
                ptype = ph.get("type", "")
                if ptype == "location" or "location" in ptype.lower():
                    job_loc = label
                elif ptype in ("salary", "ctc") or "salary" in ptype.lower():
                    salary_str = label

            # Skills from tagsAndSkills
            skills_list = [
                s.get("label", "") for s in item.get("tagsAndSkills", [])
                if s.get("label")
            ]

            jobs.append({
                "title":       item.get("title", ""),
                "company":     item.get("companyName", ""),
                "url":         job_url,
                "location":    job_loc or naukri_loc or "India",
                "description": strip_html(item.get("jobDescription", "")),
                "source":      "naukri",
                "work_type":   "remote" if item.get("isWFH") else "onsite",
                "salary_min":  None,   # Naukri salary is a string (e.g. "10-15 Lacs")
                "salary_max":  None,
                "salary_str":  salary_str,
                "skills":      skills_list,
                "tags":        skills_list[:5],
            })

        print(f"[NAUKRI] '{keyword}' → {len(jobs)} jobs")
        return jobs

    except httpx.HTTPStatusError as e:
        print(f"[NAUKRI] HTTP {e.response.status_code} for '{keyword}': {e}")
        return []
    except Exception as e:
        print(f"[NAUKRI] Error for '{keyword}': {e}")
        return []


# ─── Source 3: Adzuna India (official API, free tier) ────────────────────────

async def fetch_adzuna(
    search_term: str,
    location: str = "",
    results_per_page: int = 20,
    max_days_old: int = 7,
) -> list[dict]:
    """
    Adzuna official REST API — India coverage, includes salary data.
    Requires ADZUNA_APP_ID and ADZUNA_APP_KEY in .env (free at developer.adzuna.com).
    Skipped gracefully if keys are missing.
    """
    app_id  = getattr(settings, "ADZUNA_APP_ID", "")
    app_key = getattr(settings, "ADZUNA_APP_KEY", "")

    if not app_id or not app_key:
        print("[ADZUNA] Skipped — add ADZUNA_APP_ID and ADZUNA_APP_KEY to .env (free at developer.adzuna.com)")
        return []

    params = {
        "app_id":           app_id,
        "app_key":          app_key,
        "results_per_page": results_per_page,
        "what":             search_term,
        "max_days_old":     max_days_old,
        "content-type":     "application/json",
    }

    # Extract city from location for Adzuna's "where" param
    city = location.replace(", India", "").replace(",India", "").strip()
    if city and city.lower() not in ("india", ""):
        params["where"] = city

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",  # "in" = India
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        jobs = []
        for item in data.get("results", []):
            title = item.get("title", "")
            if not title:
                continue

            loc_data = item.get("location", {})
            loc_display = loc_data.get("display_name", location or "India")

            jobs.append({
                "title":       title,
                "company":     item.get("company", {}).get("display_name", ""),
                "url":         item.get("redirect_url", ""),
                "location":    loc_display,
                "description": strip_html(item.get("description", "")),
                "source":      "adzuna",
                "work_type":   "remote" if "remote" in title.lower() else "onsite",
                "salary_min":  item.get("salary_min"),
                "salary_max":  item.get("salary_max"),
                "skills":      [],
                "tags":        [item.get("category", {}).get("label", "")],
            })

        print(f"[ADZUNA] '{search_term}' → {len(jobs)} jobs")
        return jobs

    except httpx.HTTPStatusError as e:
        print(f"[ADZUNA] HTTP {e.response.status_code}: {e}")
        return []
    except Exception as e:
        print(f"[ADZUNA] Error: {e}")
        return []


# ─── Source 4: Remotive (remote jobs, no key, kept as bonus) ─────────────────

async def fetch_remotive(search: str = "", limit: int = 15) -> list[dict]:
    """Free remote-only jobs API. No key needed."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                "https://remotive.com/api/remote-jobs",
                params={"category": "software-dev", "limit": limit, "search": search},
            )
            resp.raise_for_status()
            data = resp.json()

        jobs = [{
            "title":       item.get("title", ""),
            "company":     item.get("company_name", ""),
            "url":         item.get("url", ""),
            "location":    item.get("candidate_required_location", "Remote"),
            "description": strip_html(item.get("description", "")),
            "source":      "remotive",
            "work_type":   "remote",
            "salary_min":  None,
            "salary_max":  None,
            "skills":      [],
            "tags":        item.get("tags", []),
        } for item in data.get("jobs", [])]

        print(f"[REMOTIVE] '{search}' → {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"[REMOTIVE] Error: {e}")
        return []


# ─── LLM Scoring ─────────────────────────────────────────────────────────────

async def score_single_job(title: str, desc: str, resume: str) -> dict:
    prompt = f"""Score this job match 0-100 for this candidate.
JOB: {title}
DESC: {desc[:800]}
CANDIDATE: {resume[:600]}
Return ONLY: {{"score": <number>, "reasoning": "<brief>"}}"""
    try:
        result = await llm_provider.generate_json(
            prompt=prompt,
            system_prompt="Return only valid JSON with score and reasoning.",
            model="openai-large",
        )
        if isinstance(result, dict) and "error" in result:
            return {"score": 0, "reasoning": "LLM parse failed"}
        score = result.get("score", 0)
        if isinstance(score, str):
            score = float(score)
        return {"score": min(max(float(score), 0), 100), "reasoning": result.get("reasoning", "")}
    except Exception as e:
        return {"score": 0, "reasoning": f"Error: {e}"}


async def batch_score_jobs(jobs_list: list[dict], resume: str, user_loc: str) -> list[dict]:
    if not jobs_list:
        return []

    lines = [
        f"[{i}] {j['title']} @ {j['company']} ({j['location']}) -- {j['description'][:200]}"
        for i, j in enumerate(jobs_list)
    ]
    prompt = f"""Score each job 0-100 for this candidate (based in {user_loc or 'India'}).

CANDIDATE: {resume[:700]}

JOBS:
{chr(10).join(lines)}

Return ONLY a JSON array: [{{"index":0,"score":85,"reasoning":"..."}}, ...]"""

    try:
        result = await llm_provider.generate_json(
            prompt=prompt, system_prompt="Return ONLY a valid JSON array. No markdown, no extra keys.",
            model="openai-large",
        )
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            if "error" in result:
                raise ValueError("LLM returned error")
            for key in ["results", "scores", "jobs", "data"]:
                if key in result and isinstance(result[key], list):
                    return result[key]
        raise ValueError("Unexpected format")
    except Exception as e:
        print(f"[SCOUT] Batch scoring failed ({e}), falling back to individual...")
        scores = []
        for i, j in enumerate(jobs_list):
            r = await score_single_job(j["title"], j["description"], resume)
            scores.append({"index": i, **r})
        return scores


# ─── Resume Helpers ───────────────────────────────────────────────────────────

def build_resume_summary(data: dict) -> str:
    parts = []
    if data.get("title"):   parts.append(f"Title: {data['title']}")
    if data.get("summary"): parts.append(f"Summary: {data['summary']}")
    if data.get("skills"):
        s = data["skills"]
        parts.append(f"Skills: {', '.join(s) if isinstance(s, list) else s}")
    for exp in (data.get("experience") or [])[:3]:
        parts.append(f"Experience: {exp.get('role','')} at {exp.get('company','')}")
    return "\n".join(parts)


def extract_skills_list(data: dict) -> list[str]:
    skills = data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]
    return [s for s in skills if len(s) > 1]


# ─── Main Scout Entry Point ───────────────────────────────────────────────────

async def run_scout(
    user_id: str,
    categories: Optional[list[str]] = None,
    min_score: float = 60.0,
    max_jobs: int = 25,
    search_term: str = "",
) -> dict:
    """
    Scout Agent v6 — India-first.

    Pipeline:
      1. Resolve India location from resume (never empty)
      2. Build smart queries from resume skills
      3. Scrape ALL sources concurrently:
           JobSpy (Indeed India + LinkedIn + Naukri + Glassdoor)
           Naukri internal API (direct JSON, no key)
           Adzuna India (official API, optional free key)
           Remotive (remote bonus)
      4. Filter: title blocklist → skills overlap
      5. Deduplicate
      6. LLM batch score
      7. Save above min_score
    """
    stats = {
        "fetched": 0, "blocked_title": 0, "blocked_skills": 0,
        "new": 0, "scored": 0, "saved": 0, "errors": 0,
        "queries_used": [], "sources": [],
        "source_counts": {},
    }

    async with async_session_factory() as db:
        run = AgentRun(
            user_id=user_id, agent_type="scout", status="running",
            config={"search": search_term, "min_score": min_score},
        )
        db.add(run)
        await db.flush()

        try:
            # 1. Load active resume
            res = await db.execute(
                select(MasterResume).where(
                    MasterResume.user_id == user_id,
                    MasterResume.is_active == True,
                )
            )
            resume = res.scalar_one_or_none()
            if not resume:
                run.status = "failed"
                run.result = {"error": "No active resume"}
                await db.commit()
                return {"error": "No active resume. Create one in the Resume tab first."}

            resume_data   = resume.resume_data or {}
            resume_text   = build_resume_summary(resume_data)
            user_skills   = extract_skills_list(resume_data)

            # 2. Always resolve to a valid India location
            raw_location  = resume_data.get("location", "")
            user_location = resolve_location(raw_location)
            print(f"[SCOUT] Location resolved: '{raw_location}' → '{user_location}'")

            # 3. Build search queries
            queries = [search_term] if search_term else build_search_queries(resume_data)
            if not queries:
                queries = ["software engineer"]   # Safe fallback
            stats["queries_used"] = queries
            print(f"[SCOUT] Queries: {queries} | Skills: {user_skills[:8]}")

            # 4. Load known URLs (dedup against existing DB)
            existing = await db.execute(
                select(JobPosting.url).where(JobPosting.user_id == user_id)
            )
            known_urls = {r[0] for r in existing.all()}

            # 5. Scrape ALL sources concurrently
            per_query  = max(max_jobs // len(queries), 15)
            primary_q  = queries[0]   # Use first query for Naukri + Adzuna

            print(f"[SCOUT] Launching all sources concurrently...")

            # Build coroutines: one jobspy call per query + naukri + adzuna + remotive
            jobspy_tasks   = [fetch_jobspy(q, user_location, per_query) for q in queries]
            naukri_task    = fetch_naukri(primary_q, user_location, results=25)
            adzuna_task    = fetch_adzuna(primary_q, user_location, results_per_page=20)
            remotive_task  = fetch_remotive(search=primary_q, limit=15)

            results = await asyncio.gather(
                *jobspy_tasks,
                naukri_task,
                adzuna_task,
                remotive_task,
                return_exceptions=True,
            )

            # Unpack results (last 3 are naukri, adzuna, remotive)
            all_jobs: list[dict] = []
            num_jobspy = len(jobspy_tasks)

            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    print(f"[SCOUT] Source {i} failed: {r}")
                    stats["errors"] += 1
                    continue
                if isinstance(r, list):
                    all_jobs.extend(r)

            # Track source counts
            for j in all_jobs:
                src = j.get("source", "unknown")
                stats["source_counts"][src] = stats["source_counts"].get(src, 0) + 1
            stats["sources"] = list(stats["source_counts"].keys())
            stats["fetched"] = len(all_jobs)
            print(f"[SCOUT] Total fetched: {stats['fetched']} | By source: {stats['source_counts']}")

            # 6. Filter Layer 1: Title blocklist
            tech_jobs = [j for j in all_jobs if is_tech_job(j["title"])]
            stats["blocked_title"] = stats["fetched"] - len(tech_jobs)
            print(f"[SCOUT] After title filter: {len(tech_jobs)} ({stats['blocked_title']} blocked)")

            # 7. Filter Layer 2: Skills overlap (≥1 skill must appear in description)
            if user_skills:
                skilled_jobs = []
                for j in tech_jobs:
                    # Also check skills field from Naukri (if present)
                    combined_text = j["description"] + " " + " ".join(j.get("skills", []))
                    overlap = skills_overlap_score(combined_text, user_skills)
                    if overlap >= 1:
                        j["_skill_overlap"] = overlap
                        skilled_jobs.append(j)
                    else:
                        stats["blocked_skills"] += 1
                # Sort by skill overlap — most relevant first
                skilled_jobs.sort(key=lambda x: x.get("_skill_overlap", 0), reverse=True)
                print(f"[SCOUT] After skills filter: {len(skilled_jobs)} ({stats['blocked_skills']} blocked)")
            else:
                skilled_jobs = tech_jobs

            # 8. Deduplicate
            seen_urls: set[str] = set()
            new_jobs: list[dict] = []
            for j in skilled_jobs:
                url = j.get("url", "")
                if url and url not in known_urls and url not in seen_urls:
                    seen_urls.add(url)
                    new_jobs.append(j)
            stats["new"] = len(new_jobs)
            print(f"[SCOUT] {stats['new']} unique new jobs to score")

            if not new_jobs:
                run.status = "completed"
                run.result = stats
                await db.commit()
                return stats

            # 9. LLM batch score in chunks of 8
            for i in range(0, len(new_jobs), 8):
                chunk = new_jobs[i:i + 8]
                try:
                    scores = await batch_score_jobs(chunk, resume_text, user_location)
                    stats["scored"] += len(scores)
                except Exception as e:
                    print(f"[SCOUT] Scoring chunk error: {e}")
                    stats["errors"] += 1
                    continue

                for item in scores:
                    idx   = item.get("index", -1)
                    score = item.get("score", 0)
                    if isinstance(score, str):
                        try:
                            score = float(score)
                        except Exception:
                            score = 0
                    score = float(score)

                    if idx < 0 or idx >= len(chunk):
                        continue

                    raw   = chunk[idx]
                    bonus = location_bonus(raw.get("location", ""), user_location)
                    final = min(score + bonus, 100)

                    if final >= min_score:
                        db.add(JobPosting(
                            user_id=user_id,
                            title=raw["title"],
                            company=raw["company"],
                            location=raw.get("location", ""),
                            url=raw["url"],
                            description=raw.get("description", ""),
                            source=raw.get("source", "unknown"),
                            work_type=raw.get("work_type", "onsite"),
                            relevance_score=round(final, 1),
                            salary_min=raw.get("salary_min"),
                            salary_max=raw.get("salary_max"),
                            requirements={
                                "tags":          raw.get("tags", []),
                                "skills":        raw.get("skills", []),
                                "reasoning":     item.get("reasoning", ""),
                                "skill_overlap": raw.get("_skill_overlap", 0),
                                "location_bonus": bonus,
                                "salary_str":    raw.get("salary_str", ""),
                            },
                            status="discovered",
                        ))
                        known_urls.add(raw["url"])
                        stats["saved"] += 1

            run.status = "completed"
            run.result = stats
            await db.commit()
            print(f"[SCOUT] ✓ Done! {stats}")

        except Exception as e:
            print(f"[SCOUT] Fatal error: {e}")
            import traceback
            traceback.print_exc()
            run.status = "failed"
            run.result = {"error": str(e)}
            await db.commit()
            raise

    return stats