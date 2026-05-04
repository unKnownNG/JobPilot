# =============================================================================
# agents/tailor.py — Tailor Agent (Resume Customization)
# =============================================================================
# The Tailor Agent:
#   1. Finds jobs with status "approved" (user wants to apply)
#   2. Reads the user's master resume
#   3. Sends job description + resume to the LLM
#   4. LLM rewrites experience bullets to match the job requirements
#   5. Saves a TailoredResume linked to that job
#   6. Creates an Application record with status "resume_ready"
# =============================================================================

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.llm import llm_provider
from app.models.job_posting import JobPosting
from app.models.resume import MasterResume, TailoredResume
from app.models.application import Application
from app.models.agent_run import AgentRun


async def tailor_resume_with_llm(master_data: dict, job_title: str, job_desc: str) -> dict:
    """
    Ask the LLM to rewrite resume content to better match a specific job.

    The LLM receives the full master resume JSON and the job description,
    then returns a modified version with:
      - Rewritten experience bullets highlighting relevant skills
      - Reordered skills (most relevant first)
      - Updated summary tailored to the role
    """
    prompt = f"""You are a professional resume writer. Tailor this resume for the job below.

JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_desc[:2000]}

MASTER RESUME (JSON):
{json.dumps(master_data, indent=2)[:3000]}

Rules:
1. Keep ALL factual information (company names, dates, education) unchanged.
2. Rewrite experience bullet points to emphasize skills mentioned in the job description.
3. Reorder the skills list so the most relevant skills appear first.
4. Rewrite the summary to target this specific role.
5. Do NOT invent fake experience or skills the candidate doesn't have.

Return ONLY the complete modified resume as valid JSON with the same structure."""

    result = await llm_provider.generate_json(
        prompt=prompt,
        system_prompt="You are an expert resume tailor. Return ONLY valid JSON matching the input structure.",
        model="claude",
    )

    # If parsing failed, return the master as fallback
    if "error" in result and "raw" in result:
        return master_data

    return result


def compute_diff(master: dict, tailored: dict) -> dict:
    """
    Compute a simple diff between master and tailored resume.
    Returns a dict showing what changed for the UI to display.
    """
    diff = {"changes": []}

    # Check summary
    if master.get("summary") != tailored.get("summary"):
        diff["changes"].append({
            "field": "summary",
            "original": (master.get("summary") or "")[:200],
            "tailored": (tailored.get("summary") or "")[:200],
        })

    # Check skills order
    master_skills = master.get("skills", [])
    tailored_skills = tailored.get("skills", [])
    if master_skills != tailored_skills:
        diff["changes"].append({
            "field": "skills",
            "original": master_skills[:10] if isinstance(master_skills, list) else str(master_skills)[:200],
            "tailored": tailored_skills[:10] if isinstance(tailored_skills, list) else str(tailored_skills)[:200],
        })

    # Check experience bullets
    master_exp = master.get("experience", [])
    tailored_exp = tailored.get("experience", [])
    for i, (m, t) in enumerate(zip(master_exp, tailored_exp)):
        m_bullets = m.get("bullets", [])
        t_bullets = t.get("bullets", [])
        if m_bullets != t_bullets:
            diff["changes"].append({
                "field": f"experience[{i}].bullets",
                "company": m.get("company", ""),
                "original_count": len(m_bullets),
                "tailored_count": len(t_bullets),
            })

    diff["total_changes"] = len(diff["changes"])
    return diff


async def run_tailor(user_id: str) -> dict:
    """
    Main tailor entry point.

    Finds all "approved" jobs, tailors the resume for each, creates
    Application records with status "resume_ready".
    """
    stats = {"processed": 0, "tailored": 0, "errors": 0, "skipped": 0}

    async with async_session_factory() as db:
        # Log agent run
        run = AgentRun(user_id=user_id, agent_type="tailor", status="running", config={})
        db.add(run)
        await db.flush()

        try:
            # 1. Get active resume
            res = await db.execute(
                select(MasterResume).where(
                    MasterResume.user_id == user_id,
                    MasterResume.is_active == True,
                )
            )
            master = res.scalar_one_or_none()
            if not master:
                run.status = "failed"
                run.result = {"error": "No active resume"}
                await db.commit()
                return {"error": "No active resume. Create one first."}

            master_data = master.resume_data or {}

            # 2. Find all approved jobs that don't already have a tailored resume
            existing_tailored = await db.execute(
                select(TailoredResume.job_posting_id).where(
                    TailoredResume.user_id == user_id
                )
            )
            already_tailored = {r[0] for r in existing_tailored.all()}

            jobs_result = await db.execute(
                select(JobPosting).where(
                    JobPosting.user_id == user_id,
                    JobPosting.status == "approved",
                )
            )
            approved_jobs = jobs_result.scalars().all()

            # 3. Tailor resume for each approved job
            for job in approved_jobs:
                stats["processed"] += 1

                if job.id in already_tailored:
                    stats["skipped"] += 1
                    continue

                try:
                    # Call LLM to tailor
                    tailored_data = await tailor_resume_with_llm(
                        master_data=master_data,
                        job_title=job.title,
                        job_desc=job.description or "",
                    )

                    # Compute diff for UI display
                    diff = compute_diff(master_data, tailored_data)

                    # Save tailored resume
                    tailored = TailoredResume(
                        user_id=user_id,
                        master_resume_id=master.id,
                        job_posting_id=job.id,
                        resume_json=tailored_data,
                        diff_from_master=diff,
                    )
                    db.add(tailored)
                    await db.flush()

                    # Create application record (or update existing)
                    existing_app = await db.execute(
                        select(Application).where(
                            Application.user_id == user_id,
                            Application.job_posting_id == job.id,
                        )
                    )
                    app = existing_app.scalar_one_or_none()

                    now = datetime.now(timezone.utc)
                    if app:
                        app.tailored_resume_id = tailored.id
                        app.status = "resume_ready"
                        app.status_history = app.status_history + [
                            {"status": "resume_ready", "at": now.isoformat(), "note": "Resume tailored by AI"}
                        ]
                        app.updated_at = now
                    else:
                        app = Application(
                            user_id=user_id,
                            job_posting_id=job.id,
                            tailored_resume_id=tailored.id,
                            status="resume_ready",
                            status_history=[
                                {"status": "queued", "at": now.isoformat(), "note": "Job approved"},
                                {"status": "resume_ready", "at": now.isoformat(), "note": "Resume tailored by AI"},
                            ],
                        )
                        db.add(app)

                    stats["tailored"] += 1

                except Exception as e:
                    print(f"[TAILOR] Error tailoring for '{job.title}': {e}")
                    stats["errors"] += 1
                    continue

            run.status = "completed"
            run.result = stats
            await db.commit()

        except Exception as e:
            run.status = "failed"
            run.result = {"error": str(e)}
            await db.commit()
            raise

    return stats
