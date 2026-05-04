# =============================================================================
# core/resume_parser.py — Resume File Parser (PDF / DOCX / TXT)
# =============================================================================
# Extracts raw text from an uploaded file, then sends it to the LLM to
# parse into a structured JSON resume that matches the MasterResume schema.
# =============================================================================

import io
import re
from typing import Optional

from app.core.llm import llm_provider


# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages).strip()
    except Exception as e:
        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n".join(p.extract_text() or "" for p in reader.pages).strip()
        except Exception:
            raise ValueError(f"Could not extract text from PDF: {e}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a .docx file."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        raise ValueError(f"Could not extract text from DOCX: {e}")


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name.endswith(".txt") or name.endswith(".md"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {filename}. Upload a PDF, DOCX, or TXT.")


# ─── LLM Parsing ─────────────────────────────────────────────────────────────

PARSE_SYSTEM_PROMPT = """You are an expert resume parser.
Extract all information from the resume text and return a single JSON object.
Return ONLY valid JSON — no markdown, no explanations."""

PARSE_PROMPT_TEMPLATE = """Parse the following resume text into a structured JSON object.
Use EXACTLY this structure (fill in all fields you can find, leave others as empty string or empty array):

{{
  "name": "Full Name",
  "title": "Professional Title / Role",
  "email": "email@example.com",
  "phone": "+1234567890",
  "location": "City, Country",
  "linkedin": "https://linkedin.com/in/...",
  "github": "https://github.com/...",
  "portfolio": "",
  "summary": "2-3 sentence professional summary",
  "skills": ["Python", "React", "SQL"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "location": "City",
      "bullets": [
        "Achieved X by doing Y resulting in Z",
        "Built/Led/Designed..."
      ]
    }}
  ],
  "education": [
    {{
      "institution": "University Name",
      "degree": "Bachelor of Science in Computer Science",
      "year": "2022",
      "gpa": ""
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "What it does",
      "tech_stack": ["Python", "React"],
      "url": ""
    }}
  ],
  "certifications": ["AWS Certified Solutions Architect"],
  "languages": ["English (Native)", "Hindi (Fluent)"]
}}

RESUME TEXT:
{resume_text}"""


async def parse_resume_with_llm(raw_text: str) -> dict:
    """
    Send raw resume text to Claude for structured parsing.
    Returns a dict matching the ResumeData schema.
    """
    # Truncate very long resumes to fit in the context window
    truncated = raw_text[:6000]

    prompt = PARSE_PROMPT_TEMPLATE.format(resume_text=truncated)

    result = await llm_provider.generate_json(
        prompt=prompt,
        system_prompt=PARSE_SYSTEM_PROMPT,
        model="openai-large",  # Best at strict JSON formatting
    )

    if isinstance(result, dict) and "error" in result:
        raise ValueError(f"LLM failed to parse resume: {result.get('raw', '')[:200]}")

    # Ensure skills is always a list
    if isinstance(result.get("skills"), str):
        result["skills"] = [s.strip() for s in result["skills"].split(",") if s.strip()]

    # Ensure lists are lists
    for field in ["experience", "education", "projects", "certifications", "languages"]:
        if field not in result or not isinstance(result[field], list):
            result[field] = []

    return result
