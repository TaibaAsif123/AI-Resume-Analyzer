# 📄 AI ATS Resume Analyzer

Upload a resume (PDF or DOCX), paste a job description, and get an ATS-style
compatibility score plus concrete improvement suggestions — powered by
Google Gemini.

## Features

- ATS score and job-match percentage
- Strengths, weaknesses, and missing keyword detection
- Technical vs. soft skill breakdown
- Actionable recommendations
- Downloadable text report
- Cached analysis (won't re-call the API for a repeat resume/JD pair)

## Project Structure

```
.
├── app.py                          # Streamlit UI
├── utils.py                        # Resume extraction + Gemini analysis logic
├── config.py                       # App constants (model name, limits, copy)
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example        # Template — copy to secrets.toml locally
└── README.md
```

## Setup

1. Clone the repo and install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Add your Gemini API key. Two options:

   **Local development:**
   ```
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   Then edit `.streamlit/secrets.toml` and paste your real key.

   **Or**, skip secrets entirely and paste the key into the sidebar text
   field when the app is running — useful for a quick test.

3. Run the app:
   ```
   streamlit run app.py
   ```

## Deploying on Streamlit Cloud

1. Push this repo to GitHub (make sure `app.py`, `utils.py`, `config.py`,
   and `requirements.txt` are all at the repo root).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at the repo, branch, and `app.py`.
3. Go to your app → **Manage app** → **Settings** → **Secrets**, and add:
   ```
   GEMINI_API_KEY = "your-real-key-here"
   ```
4. Deploy. Future pushes to the connected branch auto-redeploy; use
   **Manage app → Reboot app** to force a clean rebuild if a dependency
   change doesn't pick up automatically.

## Notes

- Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
- Max upload size is 5MB (configurable in `config.py`).
- Analysis results are cached for 1 hour per resume/JD/key combination.