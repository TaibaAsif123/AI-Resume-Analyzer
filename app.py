"""
AI ATS Resume Analyzer — Streamlit app.

Upload a resume (PDF/DOCX), paste a job description, and get an
ATS-style compatibility score and improvement suggestions powered
by Google Gemini.
"""

import streamlit as st

from config import (
    ALLOWED_FILE_TYPES,
    APP_DESCRIPTION,
    APP_ICON,
    APP_TITLE,
    MAX_FILE_SIZE_MB,
)
from utils import analyze_resume, extract_resume_text

# ---------------------------
# Page Configuration
# ---------------------------

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1000px;
    }
    .score-card {
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        color: white;
    }
    .score-good { background: linear-gradient(135deg, #16a34a, #15803d); }
    .score-mid  { background: linear-gradient(135deg, #ca8a04, #a16207); }
    .score-low  { background: linear-gradient(135deg, #dc2626, #b91c1c); }
    .score-number { font-size: 2.5rem; font-weight: 700; margin: 0; }
    .score-label { font-size: 0.9rem; opacity: 0.9; margin: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown(APP_DESCRIPTION)

# ---------------------------
# Sidebar — API Key
# ---------------------------

st.sidebar.header("Configuration")

try:
    secrets_api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    secrets_api_key = ""

if secrets_api_key:
    api_key = secrets_api_key
    st.sidebar.success("Gemini API key loaded from secrets.")
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    st.sidebar.caption(
        "Tip: add `GEMINI_API_KEY` to `.streamlit/secrets.toml` locally, "
        "or to your Streamlit Cloud app's Secrets settings, so you don't "
        "have to paste this every time."
    )

st.sidebar.divider()
st.sidebar.markdown(
    "**How it works**\n"
    "1. Upload your resume (PDF or DOCX)\n"
    "2. Paste the job description\n"
    "3. Click Analyze — Gemini scores your match and suggests improvements"
)

# ---------------------------
# Resume Upload
# ---------------------------

uploaded_file = st.file_uploader("Upload Resume", type=ALLOWED_FILE_TYPES)

if uploaded_file is not None:
    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File is {size_mb:.1f}MB — please upload something under {MAX_FILE_SIZE_MB}MB.")
        st.stop()

job_description = st.text_area("Paste Job Description", height=250)

analyze_button = st.button("Analyze Resume", type="primary")

# ---------------------------
# Analysis
# ---------------------------

if analyze_button:

    if not api_key:
        st.error("Please enter your Gemini API Key.")
        st.stop()

    if uploaded_file is None:
        st.error("Please upload a resume.")
        st.stop()

    if job_description.strip() == "":
        st.error("Please paste a job description.")
        st.stop()

    progress = st.progress(0, text="Extracting resume text...")
    resume_text = extract_resume_text(uploaded_file)
    progress.progress(50, text="Analyzing with Gemini...")

    if resume_text == "":
        progress.empty()
        st.error("Unable to extract text from the uploaded resume.")
        st.stop()

    result = analyze_resume(resume_text, job_description, api_key)
    progress.progress(100, text="Done!")
    progress.empty()

    if result is None:
        st.stop()

    # -----------------------
    # Score Dashboard
    # -----------------------

    st.success("Analysis Complete")

    def _score_class(score: int) -> str:
        if score >= 75:
            return "score-good"
        elif score >= 50:
            return "score-mid"
        return "score-low"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="score-card {_score_class(result['ats_score'])}">
                <p class="score-number">{result['ats_score']}/100</p>
                <p class="score-label">ATS Score</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="score-card {_score_class(result['match_percentage'])}">
                <p class="score-number">{result['match_percentage']}%</p>
                <p class="score-label">Job Match</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("Resume Summary")
    st.write(result["summary"])

    tab1, tab2, tab3 = st.tabs(["Strengths & Weaknesses", "Skills", "Recommendations"])

    with tab1:
        col_s, col_w = st.columns(2)
        with col_s:
            st.markdown("**✅ Strengths**")
            for item in result["strengths"]:
                st.markdown(f"- {item}")
        with col_w:
            st.markdown("**⚠️ Weaknesses**")
            for item in result["weaknesses"]:
                st.markdown(f"- {item}")

        st.markdown("**🔑 Missing Keywords**")
        if result["missing_keywords"]:
            st.write(", ".join(result["missing_keywords"]))
        else:
            st.success("No major keywords missing.")

    with tab2:
        col_t, col_soft = st.columns(2)
        with col_t:
            st.markdown("**Technical Skills**")
            st.write(", ".join(result["technical_skills"]) or "—")
        with col_soft:
            st.markdown("**Soft Skills**")
            st.write(", ".join(result["soft_skills"]) or "—")

    with tab3:
        for rec in result["recommendations"]:
            st.info(rec)

    # -----------------------
    # Downloadable Report
    # -----------------------

    report_lines = [
        "AI ATS Resume Analyzer Report",
        "================================",
        f"ATS Score: {result['ats_score']}/100",
        f"Match Percentage: {result['match_percentage']}%",
        "",
        "Summary:",
        result["summary"],
        "",
        "Strengths:",
        *[f"- {s}" for s in result["strengths"]],
        "",
        "Weaknesses:",
        *[f"- {w}" for w in result["weaknesses"]],
        "",
        "Missing Keywords:",
        ", ".join(result["missing_keywords"]) or "None",
        "",
        "Recommendations:",
        *[f"- {r}" for r in result["recommendations"]],
    ]

    st.download_button(
        "Download Report (.txt)",
        data="\n".join(report_lines),
        file_name="resume_analysis_report.txt",
        mime="text/plain",
    )