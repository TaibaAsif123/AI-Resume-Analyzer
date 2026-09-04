"""
Configuration constants for the AI ATS Resume Analyzer.

Centralizing these makes it easy to tweak behavior (model name, limits,
copy) without hunting through app.py or utils.py.
"""

APP_TITLE = "AI ATS Resume Analyzer"
APP_ICON = "📄"
APP_DESCRIPTION = "Upload your resume and compare it with a job description using Google Gemini."

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_TEMPERATURE = 0.3

MAX_FILE_SIZE_MB = 5
ALLOWED_FILE_TYPES = ["pdf", "docx"]

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2