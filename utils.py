import json
import re
import pdfplumber
import docx
import google.generativeai as genai


# ---------------------------
# Resume Text Extraction
# ---------------------------

def extract_resume_text(uploaded_file):
    """
    Extracts raw text from an uploaded PDF or DOCX resume file.
    Returns an empty string if extraction fails.
    """
    try:
        filename = uploaded_file.name.lower()

        if filename.endswith(".pdf"):
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()

        elif filename.endswith(".docx"):
            document = docx.Document(uploaded_file)
            text = "\n".join(
                paragraph.text for paragraph in document.paragraphs if paragraph.text
            )
            return text.strip()

        else:
            return ""

    except Exception as e:
        print(f"Error extracting resume text: {e}")
        return ""


# ---------------------------
# Gemini-based Resume Analysis
# ---------------------------

def _build_prompt(resume_text, job_description):
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


def _parse_json_response(raw_text):
    """
    Cleans and parses a JSON object out of the model's raw text response,
    even if it's wrapped in markdown code fences.
    """
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()

    # Fallback: grab the first {...} block if there's stray text around it
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)

    return json.loads(cleaned)


def analyze_resume(resume_text, job_description):
    """
    Sends the resume and job description to Gemini Flash and returns a
    parsed dictionary with ATS score, match percentage, and analysis details.
    Returns None if the call or parsing fails.
    """
    try:
        model = genai.GenerativeModel("gemini-3.6-flash")

        prompt = _build_prompt(resume_text, job_description)

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )

        result = _parse_json_response(response.text)

        # Ensure all expected keys exist, defaulting safely if the model omits any
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
        print(f"Error analyzing resume: {e}")
        return None