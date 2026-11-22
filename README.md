# Tarang AI — Lightweight Portfolio Command Center

## Run on Windows
1. Extract the ZIP.
2. Open PowerShell in this folder.
3. Create/activate a virtual environment:
   ```powershell
   py -m venv .venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```
4. Install:
   ```powershell
   pip install -r requirements.txt
   ```
5. Run:
   ```powershell
   streamlit run app.py
   ```

No API key, API credits, external AI service or internet connection is needed after dependencies are installed.

## Features
- Synthetic dataset for 12 clients and 16 inbox records.
- Rule-based priority score and ranked action queue.
- Keyword-based sentiment indicators.
- Recurring-issue signals.
- Templated recommended next actions.
- Portfolio view and downloadable weekly brief.

## Important honesty note
This version is a lightweight local automation prototype, not an LLM-powered AI system. Sentiment and recurrence use keyword heuristics; recommendations use transparent rules. Describe it accurately in the pitch as AI-assisted workflow automation / rules-based decision support, not as a live generative AI integration.

All data is synthetic. Portfolio ACV includes invented demonstration accounts and must not be confused with the case's stated ₹3.40 Cr existing ACV for the six named client situations.
