# =============================================================================
# agents/scout.py — Scout Agent (Job Discovery + AI Scoring)
# =============================================================================
# Improvements over v1:
#   - BATCH scoring: sends multiple jobs to LLM in one call (5-10x faster)
#   - Location filtering: prioritizes jobs matching user's city/state/country
#   - Pulls user location from their resume automatically
# =============================================================================

import re
import json
import httpx
from typing import Optional
from html import unescape

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.llm import llm_provider
from app.models.job_posting import JobPosting
from app.models.resume import MasterResume
from app.models.agent_run import AgentRun


REMOTIVE_API = "https://remotive.com/api/remote-jobs"
DEFAULT_CATEGORIES = ["software-dev", "data", "devops"]

# Common location keywords to help with matching
INDIA_KEYWORDS = ["india", "bangalore", "bengaluru", "hyderabad", "mumbai", "pune",
                  "delhi", "chennai", "noida", "gurgaon", "gurugram", "kolkata",
                  "ahmedabad", "jaipur", "kochi", "chandigarh", "asia", "apac"]


def strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1500]


def location_matches(job_location: str, user_location: str) -> bool:
    """
    Check if a job's location is compatible with the user's location.
    Returns True if:
      - Job is listed as "Anywhere" / "Worldwide"
      - Job location contains the user's country, state, or city
      - Job location is empty (assumed remote/global)
    """
    if not job_location or not user_location:
        return True

    job_loc = job_location.lower().strip()
    user_loc = user_location.lower().strip()

    # Always accept worldwide/anywhere jobs
    global_keywords = ["anywhere", "worldwide", "global", "remote"]
    if any(kw in job_loc for kw in global_keywords):
        return True

    # Check if user's location tokens appear in job location
    user_tokens = [t.strip() for t in re.split(r"[,\s]+", user_loc) if len(t.strip()) > 2]
    for token in user_tokens:
        if token in job_loc:
            return True

    # Special handling: if user is in India, also check common Indian city names
    if any(kw in user_loc for kw in ["india", "bengaluru", "bangalore", "mumbai", "hyderabad",
                                      "pune", "delhi", "chennai", "noida", "kolkata"]):
        if any(kw in job_loc for kw in INDIA_KEYWORDS):
            return True

    return False


async def fetch_remotive_jobs(category: str = "software-dev", limit: int = 25, search: str = "") -> list[dict]:
    """Fetch jobs from the free Remotive API with optional search term."""
    params = {"category": category, "limit": limit}
    if search:
        params["search"] = search

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(REMOTIVE_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("jobs", []):
        jobs.append({
            "title": item.get("title", ""),
            "company": item.get("company_name", ""),
            "url": item.get("url", ""),
            "location": item.get("candidate_required_location", "Anywhere"),
            "description": strip_html(item.get("description", "")),
            "source": "remotive",
            "work_type": "remote",
            "tags": item.get("tags", []),
        })
    return jobs


async def batch_score_jobs(jobs: list[dict], resume_summary: str, user_location: str) -> list[dict]:
    """
    Score multiple jobs in a SINGLE LLM call (much faster than one-by-one).
    Returns a list of {index, score, reasoning} dicts.
    """
    if not jobs:
        return []

    # Build a compact job list for the prompt
    job_lines = []
    for i, j in enumerate(jobs):
        job_lines.append(f"[{i}] {j['title']} at {j['company']} ({j['location']}) — {j['description'][:300]}")

    jobs_text = "\n".join(job_lines)

    prompt = f"""Score each job below for this candidate. The candidate is based in "{user_location}".
Prefer jobs that match the candidate's location or are listed as remote/worldwide.

CANDIDATE:
{resume_summary[:800]}

JOBS:
{jobs_text}

Return ONLY a valid JSON array. Each element: {{"index": <number>, "score": <0-100>, "reasoning": "<brief>"}}
Example: [{{"index": 0, "score": 85, "reasoning": "Strong Python match, remote OK"}}]"""

    result = await llm_provider.generate_json(
        prompt=prompt,
        system_prompt="You are a job-matching AI. Return ONLY a valid JSON array, no markdown.",
    )

    # Handle both list and dict responses
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        # Sometimes LLM wraps in {"results": [...]} or {"scores": [...]}
        for key in ["results", "scores", "jobs", "data"]:
            if key in result and isinstance(result[key], list):
                return result[key]
        # If it returned a single score dict, wrap it
        if "score" in result:
            return [result]
    return []


def build_resume_summary(data: dict) -> str:
    """Convert resume JSON to a compact text summary for the LLM."""
    parts = []
    if data.get("title"): parts.append(f"Title: {data['title']}")
    if data.get("summary"): parts.append(f"Summary: {data['summary']}")
    if data.get("skills"):
        s = data["skills"]
        parts.append(f"Skills: {', '.join(s) if isinstance(s, list) else s}")
    for exp in (data.get("experience") or [])[:3]:
        parts.append(f"Experience: {exp.get('role','')} at {exp.get('company','')}")
    return "\n".join(parts)


async def run_scout(
    user_id: str,
    categories: Optional[list[str]] = None,
    min_score: float = 60.0,
    max_jobs: int = 20,
    search_term: str = "",
) -> dict:
    """
    Main scout entry point (v2 — faster with batch scoring + location filtering).

    Flow:
      1. Load user's resume + extract their location
      2. Fetch jobs from Remotive
      3. Filter by location compatibility
      4. Deduplicate against existing DB jobs
      5. Batch-score remaining jobs with ONE LLM call per category
      6. Save jobs scoring above min_score
    """
    cats = categories or DEFAULT_CATEGORIES
    stats = {"fetched": 0, "location_filtered": 0, "new": 0, "scored": 0, "saved": 0, "errors": 0}

    async with async_session_factory() as db:
        run = AgentRun(user_id=user_id, agent_type="scout", status="running",
                       config={"categories": cats, "min_score": min_score, "search": search_term})
        db.add(run)
        await db.flush()

        try:
            # 1. Get active resume
            res = await db.execute(
                select(MasterResume).where(MasterResume.user_id == user_id, MasterResume.is_active == True)
            )
            resume = res.scalar_one_or_none()
            if not resume:
                run.status = "failed"
                run.result = {"error": "No active resume"}
                await db.commit()
                return {"error": "No active resume. Create one in the Resume tab first."}

            resume_data = resume.resume_data or {}
            resume_text = build_resume_summary(resume_data)
            user_location = resume_data.get("location", "")

            # 2. Get existing URLs to skip duplicates
            existing = await db.execute(select(JobPosting.url).where(JobPosting.user_id == user_id))
            known_urls = {r[0] for r in existing.all()}

            # 3. Fetch, filter, batch-score, save
            for cat in cats:
                try:
                    raw_jobs = await fetch_remotive_jobs(category=cat, limit=max_jobs, search=search_term)
                    stats["fetched"] += len(raw_jobs)
                except Exception as e:
                    print(f"[SCOUT] Fetch error ({cat}): {e}")
                    stats["errors"] += 1
                    continue

                # Location filter: keep only jobs compatible with user's location
                if user_location:
                    filtered = [j for j in raw_jobs if location_matches(j["location"], user_location)]
                    stats["location_filtered"] += len(raw_jobs) - len(filtered)
                    raw_jobs = filtered

                # Remove duplicates
                new_jobs = [j for j in raw_jobs if j["url"] not in known_urls]
                stats["new"] += len(new_jobs)

                if not new_jobs:
                    continue

                # Batch score in chunks of 10 (keeps prompt size manageable)
                for i in range(0, len(new_jobs), 10):
                    chunk = new_jobs[i:i+10]
                    try:
                        scores = await batch_score_jobs(chunk, resume_text, user_location)
                        stats["scored"] += len(scores)
                    except Exception as e:
                        print(f"[SCOUT] Batch score error: {e}")
                        stats["errors"] += 1
                        continue

                    # Match scores back to jobs and save
                    for score_item in scores:
                        idx = score_item.get("index", -1)
                        score = score_item.get("score", 0)
                        if isinstance(score, str):
                            try: score = float(score)
                            except: score = 0

                        if idx < 0 or idx >= len(chunk):
                            continue

                        raw = chunk[idx]
                        if score >= min_score:
                            db.add(JobPosting(
                                user_id=user_id, title=raw["title"], company=raw["company"],
                                location=raw["location"], url=raw["url"], description=raw["description"],
                                source="remotive", work_type="remote", relevance_score=score,
                                requirements={"tags": raw.get("tags", []),
                                              "reasoning": score_item.get("reasoning", "")},
                                status="discovered",
                            ))
                            known_urls.add(raw["url"])
                            stats["saved"] += 1

            run.status = "completed"
            run.result = stats
            await db.commit()

        except Exception as e:
            run.status = "failed"
            run.result = {"error": str(e)}
            await db.commit()
            raise

    return stats
