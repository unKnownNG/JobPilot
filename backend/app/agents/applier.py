# =============================================================================
# agents/applier.py — Applier Agent (Extension-Based Architecture)
# =============================================================================
# Instead of a headless browser (Playwright), the Applier Agent now works
# as a backend API that a Chrome Extension calls:
#
#   1. Extension scrapes the form HTML on the current page
#   2. Sends it to POST /api/agents/applier/analyze-form
#   3. Backend uses LLM to map resume fields → form fields
#   4. Extension fills the form using the returned instructions
#   5. Extension reports the result back via POST /api/agents/applier/log
#
# This approach solves authentication, CAPTCHA, and bot-detection issues
# because it runs inside the user's real browser session.
# =============================================================================

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_provider
import app.models  # noqa: F401 — register all models
from app.models.user import User
from app.models.resume import MasterResume, TailoredResume
from app.models.application import Application
from app.models.job_posting import JobPosting
from app.models.agent_run import AgentRun
from app.core.database import async_session_factory


# ─── LLM Form Analysis ──────────────────────────────────────────────────────

FORM_ANALYSIS_SYSTEM = """You are an expert at analyzing job application form HTML.
You receive a simplified representation of form fields and the user's resume data.
Your job is to return a JSON object mapping each form field to the correct value
from the user's resume.

Rules:
- Return ONLY valid JSON. No markdown, no explanation.
- Use the field's id, name, or label to determine what data goes there.
- For <select> dropdowns, choose the closest matching option value.
- For radio buttons, choose the correct value.
- For textareas asking "why do you want to work here" or similar, write a brief
  2-3 sentence answer using the user's background.
- If you cannot determine what a field needs, set its value to null.
- For file upload fields, set value to "__RESUME_UPLOAD__" (the extension handles this).
"""

FORM_ANALYSIS_PROMPT = """Analyze this job application form and map each field to the correct value.

## USER RESUME DATA:
{resume_json}

## FORM FIELDS:
{form_fields}

## JOB CONTEXT:
Title: {job_title}
Company: {company}
Description: {job_description}

Return a JSON object with this structure:
{{
  "field_mappings": [
    {{
      "selector": "<CSS selector or field identifier>",
      "field_type": "input|select|textarea|radio|checkbox|file",
      "value": "<value to fill>",
      "confidence": "high|medium|low",
      "reasoning": "<brief explanation>"
    }}
  ],
  "unmapped_fields": [
    {{
      "selector": "<CSS selector>",
      "label": "<field label text>",
      "reason": "Could not determine the appropriate value"
    }}
  ],
  "summary": "Mapped X of Y fields successfully"
}}"""


async def analyze_form_fields(
    form_fields: list[dict],
    resume_data: dict,
    job_title: str = "",
    company: str = "",
    job_description: str = "",
) -> dict:
    """
    Use LLM to analyze form fields and map them to resume data.

    Args:
        form_fields: List of dicts describing each form field, e.g.:
            [{"selector": "#first_name", "type": "text", "name": "first_name",
              "label": "First Name", "required": true, "options": null}]
        resume_data: The user's master resume data dict.
        job_title: Title of the job being applied to.
        company: Company name.
        job_description: First ~500 chars of the JD.

    Returns:
        Dict with field_mappings, unmapped_fields, and summary.
    """
    import json

    # Truncate job description to save tokens
    job_desc_truncated = (job_description or "")[:500]

    prompt = FORM_ANALYSIS_PROMPT.format(
        resume_json=json.dumps(resume_data, indent=2)[:3000],
        form_fields=json.dumps(form_fields, indent=2)[:3000],
        job_title=job_title or "Unknown",
        company=company or "Unknown",
        job_description=job_desc_truncated or "Not provided",
    )

    result = await llm_provider.generate_json(
        prompt=prompt,
        system_prompt=FORM_ANALYSIS_SYSTEM,
        model="openai-large",
    )

    if isinstance(result, dict) and "error" in result:
        return {
            "field_mappings": [],
            "unmapped_fields": [],
            "summary": f"LLM analysis failed: {result.get('raw', '')[:200]}",
            "error": True,
        }

    # Ensure expected structure
    if "field_mappings" not in result:
        result["field_mappings"] = []
    if "unmapped_fields" not in result:
        result["unmapped_fields"] = []
    if "summary" not in result:
        mapped_count = len(result["field_mappings"])
        total = mapped_count + len(result["unmapped_fields"])
        result["summary"] = f"Mapped {mapped_count} of {total} fields"

    return result


# ─── Get Autofill Data ──────────────────────────────────────────────────────

async def get_autofill_data(user_id: str, job_id: Optional[str] = None) -> dict:
    """
    Retrieve the user's resume data formatted for form filling.
    If a job_id is provided and a tailored resume exists, use that instead.

    Returns a dict with all the fields the extension might need:
        name, email, phone, location, linkedin, github, skills, summary,
        experience, education, etc.
    """
    async with async_session_factory() as db:
        # Get user
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            return {"error": "User not found"}

        # Try tailored resume first (if job_id provided)
        resume_data = None
        if job_id:
            tr_res = await db.execute(
                select(TailoredResume).where(
                    TailoredResume.user_id == user_id,
                    TailoredResume.job_posting_id == job_id,
                ).order_by(TailoredResume.created_at.desc()).limit(1)
            )
            tailored = tr_res.scalar_one_or_none()
            if tailored:
                resume_data = tailored.resume_json

        # Fallback to master resume
        if not resume_data:
            mr_res = await db.execute(
                select(MasterResume).where(
                    MasterResume.user_id == user_id,
                    MasterResume.is_active == True,
                )
            )
            master = mr_res.scalar_one_or_none()
            if master:
                resume_data = master.resume_data

        if not resume_data:
            return {"error": "No resume found. Please upload a resume first."}

        # Build a flat autofill-friendly dict
        name = resume_data.get("name", user.name or "")
        name_parts = name.split(" ", 1)

        return {
            "full_name": name,
            "first_name": name_parts[0] if name_parts else "",
            "last_name": name_parts[1] if len(name_parts) > 1 else "",
            "email": resume_data.get("email", user.email or ""),
            "phone": resume_data.get("phone", ""),
            "location": resume_data.get("location", ""),
            "title": resume_data.get("title", ""),
            "summary": resume_data.get("summary", ""),
            "linkedin": resume_data.get("linkedin", ""),
            "github": resume_data.get("github", ""),
            "portfolio": resume_data.get("portfolio", ""),
            "skills": resume_data.get("skills", []),
            "experience": resume_data.get("experience", []),
            "education": resume_data.get("education", []),
            "projects": resume_data.get("projects", []),
            "certifications": resume_data.get("certifications", []),
            "languages": resume_data.get("languages", []),
            # Convenient pre-formatted strings
            "skills_csv": ", ".join(resume_data.get("skills", [])),
            "latest_company": (
                resume_data.get("experience", [{}])[0].get("company", "")
                if resume_data.get("experience") else ""
            ),
            "latest_role": (
                resume_data.get("experience", [{}])[0].get("role", "")
                if resume_data.get("experience") else ""
            ),
            "highest_degree": (
                resume_data.get("education", [{}])[0].get("degree", "")
                if resume_data.get("education") else ""
            ),
            "university": (
                resume_data.get("education", [{}])[0].get("institution", "")
                if resume_data.get("education") else ""
            ),
        }


# ─── Log Application Result ────────────────────────────────────────────────

async def log_application_from_extension(
    user_id: str,
    job_url: str,
    job_title: str,
    company: str,
    status: str = "applied",
    fields_filled: list[str] | None = None,
    notes: str = "",
) -> dict:
    """
    Called by the Chrome Extension after it fills out a form.
    Creates or updates an Application record so the dashboard stays in sync.
    """
    async with async_session_factory() as db:
        # Find the matching job posting (by URL)
        job_res = await db.execute(
            select(JobPosting).where(
                JobPosting.user_id == user_id,
                JobPosting.url == job_url,
            )
        )
        job = job_res.scalar_one_or_none()

        # If the job doesn't exist in our DB, create a minimal record
        if not job:
            job = JobPosting(
                user_id=user_id,
                title=job_title or "Unknown Position",
                company=company or "Unknown Company",
                url=job_url,
                source="chrome_extension",
                status="applied",
            )
            db.add(job)
            await db.flush()

        # Check if application already exists
        app_res = await db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.job_posting_id == job.id,
            )
        )
        app = app_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if app:
            # Update existing application
            app.status = status
            app.notes = notes or f"Applied via Chrome Extension. Fields: {', '.join(fields_filled or [])}"
            app.status_history = (app.status_history or []) + [
                {
                    "status": status,
                    "at": now.isoformat(),
                    "note": f"Extension: {notes}" if notes else "Applied via Chrome Extension",
                    "source": "chrome_extension",
                }
            ]
            if status == "applied":
                app.applied_at = now
            app.platform = "chrome_extension"
            app.updated_at = now
        else:
            # Create new application
            app = Application(
                user_id=user_id,
                job_posting_id=job.id,
                status=status,
                platform="chrome_extension",
                notes=notes or f"Applied via Chrome Extension. Fields: {', '.join(fields_filled or [])}",
                status_history=[
                    {
                        "status": status,
                        "at": now.isoformat(),
                        "note": "Applied via Chrome Extension",
                        "source": "chrome_extension",
                    }
                ],
                applied_at=now if status == "applied" else None,
            )
            db.add(app)

        # Log agent run
        run = AgentRun(
            user_id=user_id,
            agent_type="applier",
            status="completed",
            config={"source": "chrome_extension", "job_url": job_url},
            result={
                "job_title": job_title,
                "company": company,
                "status": status,
                "fields_filled": fields_filled or [],
            },
        )
        db.add(run)

        await db.commit()

        return {
            "application_id": app.id,
            "job_id": job.id,
            "status": status,
            "message": f"Application logged: {job_title} at {company}",
        }
