# =============================================================================
# agents/applier.py — Applier Agent (Browser-Based Application Automation)
# =============================================================================
# The Applier Agent:
#   1. Finds applications with status "resume_ready"
#   2. Opens the job URL in a headless Chromium browser
#   3. Takes a screenshot of the job page
#   4. Looks for "Apply" buttons and navigates to the application form
#   5. Attempts to fill in basic fields (name, email, phone)
#   6. Takes a screenshot of the result
#   7. Updates application status to "applied" or "failed_to_apply"
#
# NOTE: Uses Playwright SYNC API in a background thread because Windows
# doesn't support asyncio subprocess spawning inside uvicorn's event loop.
# =============================================================================

import os
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

from app.core.database import async_session_factory
import app.models  # noqa: F401 — registers all models for SQLAlchemy relationships
from app.models.user import User
from app.models.job_posting import JobPosting
from app.models.application import Application
from app.models.resume import MasterResume, TailoredResume
from app.models.agent_run import AgentRun
from app.config import settings


# Storage for screenshots
SCREENSHOT_DIR = Path(settings.STORAGE_DIR) / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Thread pool for running sync Playwright
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="applier")

# Common "Apply" button selectors (covers most job sites)
APPLY_SELECTORS = [
    'a:has-text("Apply")',
    'button:has-text("Apply")',
    'a:has-text("Apply Now")',
    'button:has-text("Apply Now")',
    'a:has-text("Apply for this job")',
    'button:has-text("Submit Application")',
    'a:has-text("Easy Apply")',
    'button:has-text("Easy Apply")',
    '[data-testid*="apply"]',
    '[class*="apply-button"]',
    '[id*="apply"]',
]

# Common form field selectors
FIELD_SELECTORS = {
    "name": [
        'input[name*="name" i]',
        'input[id*="name" i]',
        'input[placeholder*="name" i]',
        'input[aria-label*="name" i]',
        'input[name*="full_name" i]',
    ],
    "first_name": [
        'input[name*="first" i]',
        'input[id*="first" i]',
        'input[placeholder*="first" i]',
    ],
    "last_name": [
        'input[name*="last" i]',
        'input[id*="last" i]',
        'input[placeholder*="last" i]',
    ],
    "email": [
        'input[type="email"]',
        'input[name*="email" i]',
        'input[id*="email" i]',
        'input[placeholder*="email" i]',
    ],
    "phone": [
        'input[type="tel"]',
        'input[name*="phone" i]',
        'input[id*="phone" i]',
        'input[placeholder*="phone" i]',
    ],
    "resume_upload": [
        'input[type="file"][name*="resume" i]',
        'input[type="file"][name*="cv" i]',
        'input[type="file"][id*="resume" i]',
        'input[type="file"][accept*="pdf"]',
        'input[type="file"]',
    ],
}


# ─── Sync Playwright helpers (run in thread) ─────────────────────────────────

def _take_screenshot(page: Page, app_id: str, step: str) -> str:
    """Take a screenshot and return the file path."""
    filename = f"{app_id}_{step}_{int(time.time())}.png"
    filepath = str(SCREENSHOT_DIR / filename)
    page.screenshot(path=filepath, full_page=False)
    return filepath


def _try_fill_field(page: Page, selectors: list[str], value: str) -> bool:
    """Try to fill a form field using multiple possible selectors."""
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=1000):
                el.clear()
                el.fill(value)
                return True
        except Exception:
            continue
    return False


def _try_click_apply(page: Page) -> bool:
    """Try to find and click an Apply button."""
    for selector in APPLY_SELECTORS:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=2000):
                el.click()
                page.wait_for_load_state("networkidle", timeout=10000)
                return True
        except Exception:
            continue
    return False


def _apply_to_single_job(page: Page, job_url: str, job_title: str,
                          app_id: str, user_data: dict) -> dict:
    """
    Attempt to apply to a single job (SYNC — runs in thread).
    Returns a result dict with status, screenshots, and notes.
    """
    result = {
        "status": "failed_to_apply",
        "screenshots": [],
        "notes": "",
    }

    try:
        # Step 1: Navigate to job URL
        print(f"[APPLIER] Opening: {job_url}")
        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)  # Let dynamic content load

        # Screenshot: Job page
        ss1 = _take_screenshot(page, app_id, "job_page")
        result["screenshots"].append(ss1)

        # Step 2: Look for Apply button
        clicked = _try_click_apply(page)
        if clicked:
            time.sleep(2)
            ss2 = _take_screenshot(page, app_id, "apply_form")
            result["screenshots"].append(ss2)
            print(f"[APPLIER] Found Apply button for '{job_title}'")
        else:
            result["notes"] = "Could not find Apply button. Manual application needed."
            result["status"] = "failed_to_apply"
            print(f"[APPLIER] No Apply button found for '{job_title}'")
            return result

        # Step 3: Try to fill common fields
        fields_filled = []
        name = user_data.get("name", "")

        if name:
            if _try_fill_field(page, FIELD_SELECTORS["name"], name):
                fields_filled.append("name")
            else:
                parts = name.split(" ", 1)
                if _try_fill_field(page, FIELD_SELECTORS["first_name"], parts[0]):
                    fields_filled.append("first_name")
                if len(parts) > 1:
                    if _try_fill_field(page, FIELD_SELECTORS["last_name"], parts[1]):
                        fields_filled.append("last_name")

        email = user_data.get("email", "")
        if email and _try_fill_field(page, FIELD_SELECTORS["email"], email):
            fields_filled.append("email")

        phone = user_data.get("phone", "")
        if phone and _try_fill_field(page, FIELD_SELECTORS["phone"], phone):
            fields_filled.append("phone")

        # Step 4: Try to upload resume
        resume_path = user_data.get("resume_pdf_path", "")
        if resume_path and os.path.exists(resume_path):
            for selector in FIELD_SELECTORS["resume_upload"]:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        el.set_input_files(resume_path)
                        fields_filled.append("resume_upload")
                        print(f"[APPLIER] Uploaded resume: {resume_path}")
                        break
                except Exception:
                    continue

        # Screenshot: Filled form
        if fields_filled:
            ss3 = _take_screenshot(page, app_id, "filled_form")
            result["screenshots"].append(ss3)

        result["notes"] = (
            f"Fields filled: {', '.join(fields_filled) if fields_filled else 'none'}. "
            "Manual review recommended before submitting."
        )
        result["status"] = "applied" if len(fields_filled) >= 2 else "failed_to_apply"
        print(f"[APPLIER] '{job_title}': filled {fields_filled}, status={result['status']}")

    except PWTimeout:
        result["notes"] = "Page load timed out."
        print(f"[APPLIER] Timeout for '{job_title}'")
    except Exception as e:
        result["notes"] = f"Error: {str(e)[:200]}"
        print(f"[APPLIER] Error for '{job_title}': {e}")

    return result


def _run_browser_jobs(job_infos: list[dict], user_data: dict) -> list[dict]:
    """
    Run all browser jobs synchronously (called from a thread).
    Each job_info has: url, title, app_id, pdf_path
    Returns a list of result dicts.
    """
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            for info in job_infos:
                user_data["resume_pdf_path"] = info.get("pdf_path", "")
                page = context.new_page()
                try:
                    res = _apply_to_single_job(
                        page,
                        job_url=info["url"],
                        job_title=info["title"],
                        app_id=info["app_id"],
                        user_data=user_data,
                    )
                    results.append({"app_id": info["app_id"], **res})
                except Exception as e:
                    print(f"[APPLIER] Error on '{info['title']}': {e}")
                    results.append({
                        "app_id": info["app_id"],
                        "status": "failed_to_apply",
                        "screenshots": [],
                        "notes": f"Error: {str(e)[:200]}",
                    })
                finally:
                    page.close()

            browser.close()

    except Exception as e:
        err_msg = str(e)
        if "Executable doesn't exist" in err_msg or "browserType.launch" in err_msg:
            err_msg = "Chromium not installed. Run: python -m playwright install chromium"
        print(f"[APPLIER] Browser error: {err_msg}")
        # Return error for all remaining jobs
        for info in job_infos:
            if not any(r["app_id"] == info["app_id"] for r in results):
                results.append({
                    "app_id": info["app_id"],
                    "status": "failed_to_apply",
                    "screenshots": [],
                    "notes": f"Browser error: {err_msg}",
                })

    return results


# ─── Main entry point ────────────────────────────────────────────────────────

async def run_applier(user_id: str, max_applications: int = 5) -> dict:
    """
    Main applier entry point.

    1. Finds applications with status "resume_ready"
    2. Collects job URLs and user data from DB (async)
    3. Runs Playwright SYNC in a background thread
    4. Updates application records with results (async)
    """
    stats = {"processed": 0, "applied": 0, "failed": 0, "errors": 0, "skipped": 0}

    async with async_session_factory() as db:
        # Log agent run
        run = AgentRun(
            user_id=user_id, agent_type="applier", status="running",
            config={"max_applications": max_applications},
        )
        db.add(run)
        await db.flush()

        try:
            # 1. Find "resume_ready" applications
            result = await db.execute(
                select(Application).where(
                    Application.user_id == user_id,
                    Application.status == "resume_ready",
                ).limit(max_applications)
            )
            apps = result.scalars().all()

            if not apps:
                run.status = "completed"
                run.result = {"message": "No applications with resume_ready status", **stats}
                await db.commit()
                return stats

            # 2. Get user info
            user_res = await db.execute(select(User).where(User.id == user_id))
            user = user_res.scalar_one_or_none()
            if not user:
                run.status = "failed"
                run.result = {"error": "User not found"}
                await db.commit()
                return {"error": "User not found", **stats}

            resume_res = await db.execute(
                select(MasterResume).where(
                    MasterResume.user_id == user_id,
                    MasterResume.is_active == True,
                )
            )
            master_resume = resume_res.scalar_one_or_none()
            resume_data = master_resume.resume_data if master_resume else {}

            user_data = {
                "name": resume_data.get("name", user.name),
                "email": user.email,
                "phone": resume_data.get("phone", ""),
                "resume_pdf_path": "",
            }

            # 3. Collect job info for the browser thread
            app_map = {}  # app_id -> Application ORM object
            job_infos = []

            for app in apps:
                job_res = await db.execute(
                    select(JobPosting).where(JobPosting.id == app.job_posting_id)
                )
                job = job_res.scalar_one_or_none()
                if not job:
                    stats["skipped"] += 1
                    continue

                pdf_path = ""
                if app.tailored_resume_id:
                    tr_res = await db.execute(
                        select(TailoredResume).where(TailoredResume.id == app.tailored_resume_id)
                    )
                    tailored = tr_res.scalar_one_or_none()
                    if tailored and tailored.resume_pdf_path:
                        pdf_path = tailored.resume_pdf_path

                app_map[app.id] = app
                job_infos.append({
                    "app_id": app.id[:8],
                    "full_app_id": app.id,
                    "url": job.url,
                    "title": job.title,
                    "pdf_path": pdf_path,
                })

            if not job_infos:
                run.status = "completed"
                run.result = {"message": "No valid jobs found for applications", **stats}
                await db.commit()
                return stats

            # 4. Run Playwright in a background thread (sync API)
            print(f"[APPLIER] Launching browser for {len(job_infos)} job(s)...")
            loop = asyncio.get_event_loop()
            browser_results = await loop.run_in_executor(
                _executor,
                _run_browser_jobs,
                job_infos,
                user_data,
            )

            # 5. Update application records with results
            for br in browser_results:
                stats["processed"] += 1
                # Find the matching app
                full_id = None
                for info in job_infos:
                    if info["app_id"] == br["app_id"]:
                        full_id = info["full_app_id"]
                        break
                if not full_id or full_id not in app_map:
                    stats["errors"] += 1
                    continue

                app = app_map[full_id]
                now = datetime.now(timezone.utc)
                app.status = br["status"]
                app.screenshots = (app.screenshots or []) + br.get("screenshots", [])
                app.notes = br.get("notes", "")
                app.status_history = (app.status_history or []) + [
                    {
                        "status": br["status"],
                        "at": now.isoformat(),
                        "note": br.get("notes", ""),
                    }
                ]
                if br["status"] == "applied":
                    app.applied_at = now
                    stats["applied"] += 1
                else:
                    stats["failed"] += 1
                app.updated_at = now

            run.status = "completed"
            run.result = stats
            await db.commit()
            print(f"[APPLIER] Done! {stats}")

        except Exception as e:
            print(f"[APPLIER] Fatal error: {e}")
            import traceback
            traceback.print_exc()
            run.status = "failed"
            run.result = {"error": str(e)}
            await db.commit()
            return {"error": str(e), **stats}

    return stats
