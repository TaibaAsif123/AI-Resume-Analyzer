import streamlit as st
import google.generativeai as genai
from utils import (
    extract_resume_text,
    analyze_resume
)

# ---------------------------
# Page Configuration
# ---------------------------

st.set_page_config(
    page_title="ATS Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI ATS Resume Analyzer")
st.markdown(
    "Upload your resume and compare it with a job description using **Google Gemini**."
)

# ---------------------------
# Sidebar
# ---------------------------

st.sidebar.header("Configuration")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password"
)

if api_key:
    genai.configure(api_key=api_key)

# ---------------------------
# Resume Upload
# ---------------------------

uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx"]
)

job_description = st.text_area(
    "Paste Job Description",
    height=250
)

analyze_button = st.button("Analyze Resume")

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

    with st.spinner("Extracting resume..."):

        resume_text = extract_resume_text(uploaded_file)

    if resume_text == "":
        st.error("Unable to extract text from the uploaded resume.")
        st.stop()

    with st.spinner("Analyzing resume with Gemini..."):

        result = analyze_resume(
            resume_text,
            job_description
        )

    if result is None:
        st.error("Failed to analyze resume.")
        st.stop()

    # -----------------------
    # Dashboard
    # -----------------------

    st.success("Analysis Complete")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "ATS Score",
            f"{result['ats_score']}/100"
        )

    with col2:
        st.metric(
            "Match Percentage",
            f"{result['match_percentage']}%"
        )

    st.divider()

    st.subheader("Resume Summary")
    st.write(result["summary"])

    st.subheader("Strengths")

    for item in result["strengths"]:
        st.success(item)

    st.subheader("Weaknesses")

    for item in result["weaknesses"]:
        st.error(item)

    st.subheader("Missing Keywords")

    if result["missing_keywords"]:
        st.write(", ".join(result["missing_keywords"]))
    else:
        st.success("No major keywords missing.")

    st.subheader("Technical Skills")

    st.write(", ".join(result["technical_skills"]))

    st.subheader("Soft Skills")

    st.write(", ".join(result["soft_skills"]))

    st.subheader("Recommendations")

    for rec in result["recommendations"]:
        st.info(rec)