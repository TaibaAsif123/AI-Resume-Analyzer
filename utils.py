"""
Utility functions for the AI ATS Resume Analyzer.

Handles resume text extraction (PDF/DOCX) and AI-powered analysis
against a job description using Google's Gemini API.
"""

import json
import re
import time
from typing import Optional

import docx
import pdfplumber
import google.generativeai as genai
import streamlit as st

from config import GEMINI_MODEL, GEMINI_TEMPERATURE, MAX_RETRIES, RETRY_DELAY_SECONDS


# ---------------------------
# Resume Text Extraction
# ---------------------------

def extract_resume_text(uploaded_file) -> str:
    """
    Extract raw text from an uploaded PDF or DOCX resume file.

    Args:
        uploaded_file: A Streamlit UploadedFile object.

    Returns:
        The extracted text, or an empty string if extraction fails
        or the file type is unsupported.
    """
    try:
        filename = uploaded_file.name.lower()

        if filename.endswith(".pdf"):
            return _extract_pdf_text(uploaded_file)
        elif filename.endswith(".docx"):
            return _extract_docx_text(uploaded_file)
        else:
            return ""

    except Exception as e:
        st.warning(f"Could not read the uploaded file: {e}")
        return ""


def _extract_pdf_text(uploaded_file) -> str:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _extract_docx_text(uploaded_file) -> str:
    document = docx.Document(uploaded_file)
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs).strip()


# ---------------------------
# Gemini-based Resume Analysis
# ---------------------------

def _build_prompt(resume_text: str, job_description: str) -> str:
    return f"""
You are an expert ATS (Applicant Tracking System) and technical recruiter.
Analyze the resume below against the provided job description.

Return ONLY a valid JSON object (no markdown, no code fences, no extra text)
with EXACTLY this structure:

{{
  "ats_score": <integer 0-100>,
  "match_percentage": <integer 0-100>,
  "summary": "<2-3 sentence summary of the candidate>",
  "strengths": ["<strength 1>", "<strength 2>", "..."],
  "weaknesses": ["<weakness 1>", "<weakness 2>", "..."],
  "missing_keywords": ["<keyword 1>", "<keyword 2>", "..."],
  "technical_skills": ["<skill 1>", "<skill 2>", "..."],
  "soft_skills": ["<skill 1>", "<skill 2>", "..."],
  "recommendations": ["<recommendation 1>", "<recommendation 2>", "..."]
}}

Resume:
\"\"\"
{resume_text}
\"\"\"

Job Description:
\"\"\"
{job_description}
\"\"\"
"""


def _parse_json_response(raw_text: str) -> dict:
    """Clean and parse a JSON object out of the model's raw text response."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)

    return json.loads(cleaned)


@st.cache_data(show_spinner=False, ttl=3600)
def analyze_resume(resume_text: str, job_description: str, api_key: str) -> Optional[dict]:
    """
    Send the resume and job description to Gemini and return a parsed
    analysis dict. Cached for an hour so re-running the same resume/JD
    pair doesn't burn API quota.

    Args:
        resume_text: Extracted plain text of the resume.
        job_description: The job description to compare against.
        api_key: Gemini API key (part of the cache key, so switching
            keys never serves a stale cached result from a different key).

    Returns:
        A dict with ats_score, match_percentage, summary, strengths,
        weaknesses, missing_keywords, technical_skills, soft_skills,
        and recommendations — or None if analysis fails after retries.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = _build_prompt(resume_text, job_description)

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": GEMINI_TEMPERATURE,
                    "response_mime_type": "application/json",
                },
            )
            result = _parse_json_response(response.text)

            defaults = {
                "ats_score": 0,
                "match_percentage": 0,
                "summary": "",
                "strengths": [],
                "weaknesses": [],
                "missing_keywords": [],
                "technical_skills": [],
                "soft_skills": [],
                "recommendations": [],
            }
            for key, default_value in defaults.items():
                result.setdefault(key, default_value)

            return result

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue

    st.error(f"Gemini analysis failed after {MAX_RETRIES + 1} attempt(s): {last_error}")
    return None