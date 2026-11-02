# Two-Agent Demo Checklist

Before the presentation, run `setup_windows.bat` once (internet needed for packages), then `start_backend.bat` and `start_frontend.bat` in two separate windows.

## 1. Profile (30 seconds)
- Open the Profile tab, set interests to `agentic AI, machine learning, RAG, cloud` and target role to `AI / ML Engineer`.
- Save. This becomes persistent local memory.

## 2. DailyTechUpgradeAgent (1 minute)
- Select **Offline article snapshot** and click **Generate my daily top 3**.
- Point out three published October 2026 articles, each with a summary, article link, and why it matches interests. State explicitly these are historical examples, not today's feed.
- With internet, switch to **Live RSS** for real article titles, dates and links.
- Mark an article as read and show that it is saved for future relevance ranking.

## 3. Career Coach (2 minutes)
- Select **Sample demo** and click **Find opportunities**.
- Show example job, research and startup scenarios (fictional). Under the interactive coaching section, choose **RAG** and **3 questions**, then click **Start a new interactive interview**.
- Enter `Retrieval searches.` for the first RAG question. Show that the agent recognizes retrieval but **asks a follow-up about grounding**.
- Answer question 2 with `Retrieved documents provide context to the language model.` Show feedback and the next targeted follow-up.
- Complete question 3, show the **finished session summary**, and download the session transcript.
- Refresh the page and load the saved conversation to show persistent session history.
- Optionally paste a real opportunity description and click **Check skill gaps**.
- With internet, try **Live jobs**. These are remote Remotive job listings, not research/internship coverage.

## 4. Progress and evaluation (45 seconds)
- Open **Career Readiness Report** and refresh. Confirm that **three answers and one completed interview session** are saved.
- Show `docs/architecture.png` and `docs/PROJECT_REPORT.md`.
- Run `python -m pytest -q` in the virtual environment; show test output.

## Suggested presentation language

"We built two separate but connected AI coworker workflows. The DailyTechUpgradeAgent reads authoritative RSS feeds, ranks the top three against our interests and learning gaps, and produces a short reading brief. The CareerCoachAgent discovers relevant jobs, analyzes posted requirements, runs a multi-turn coaching conversation with adaptive follow-up questions, saves the transcript, and adds the feedback to a progress report. We used Streamlit, FastAPI, LangGraph and a local SQLite profile and progress store, with optional Ollama for text generation. The offline article snapshot and fictional opportunity fixtures are clearly labeled; live mode accesses external RSS and job feeds. The current prototype is intentionally bounded and uses simple evaluation rules, which we documented."
