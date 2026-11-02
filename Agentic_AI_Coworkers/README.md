# My Agentic AI Coworkers — Working Starter Project

Two student-focused LangGraph workflows using **FastAPI + Streamlit**, with an **optional local Ollama/Qwen3** model and **SQLite learning memory**.

1. **DailyTechUpgradeAgent** finds and ranks three technical RSS items from recognized publisher feeds and creates an ~18-minute reading brief. Offline snapshot mode provides three **real, dated October 2026 articles** from publisher websites, labeled as a static snapshot rather than today's news. Live mode requires internet.
2. **nextLevelPersonalCoachForCareerLevel** discovers remote job listings through Remotive (live mode), compares opportunity descriptions with Users stated skills, conducts a **resumable 2–5-question interactive interview** that adapts follow-up questions to the concepts missed, provides feedback after every answer, and stores the full session and assessment results for a career-readiness report. Demo mode uses clearly labeled fictitious jobs/research/startup examples. You can paste a real internship/research/startup opportunity description for a skill-gap check.

## 1. Requirements

- Windows 10/11, macOS or Linux; Python **3.11+** recommended (Python 3.13 works with current packages).
- Internet for package installation and *live* RSS/job lookups.
- **Optional:** Ollama installed with `qwen3:1.7b`. Both agents also work in deterministic/offline demo mode without Ollama.

## 2. Easiest Windows setup (double-click)

1. Extract the ZIP to a normal folder, not inside the ZIP preview.
2. Double-click **`setup_windows.bat`** once; it creates `.venv` and installs dependencies (internet required).
3. Double-click **`start_backend.bat`**; keep that window open.
4. Double-click **`start_frontend.bat`**; keep that window open.
5. Open **http://localhost:8502**, and start with **Offline article snapshot** for articles, or **Sample demo (offline)** for career coaching.

If you want local Ollama text generation, open **`start_backend_with_ollama.bat`** *instead of* `start_backend.bat` (first make sure Ollama and `qwen3:1.7b` work).

These scripts use ports **8001/8502**.

## 3. Alternative: Windows PowerShell commands

Open the **project root** in VS Code (the folder containing `requirements.txt`).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Terminal 1 — FastAPI:** (uses port 8001)

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
```

Test: http://127.0.0.1:8001/docs

**Terminal 2 — Streamlit:** (opens port 8502)

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.port 8502
```

Open http://localhost:8502. Start with **Offline article snapshot** for articles, or **Sample demo (offline)** for career coaching. Both agents have ready-to-run offline data.

### Optional local AI text generation

In Terminal 1 (restart FastAPI afterward):

```powershell
$env:USE_OLLAMA = "1"
$env:OLLAMA_MODEL = "qwen3:1.7b"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
```

First install/start Ollama and run `ollama pull qwen3:1.7b`. With `USE_OLLAMA=1`, the agent asks Qwen to summarize RSS excerpts and give additional coaching feedback; otherwise, a transparent fast rules-based version works. Ollama inference may be slow on older laptops. Set `USE_OLLAMA=0` for a fast demo.

### Mac/Linux

Use `python3 -m venv .venv`, `source .venv/bin/activate`, then `pip install -r requirements.txt`; run `python -m uvicorn backend.main:app --reload --port 8001` and `python -m streamlit run frontend/app.py --server.port 8502` in separate terminals.

## 4. Demonstrate both agents

1. In **My Profile**, set Users interests, existing skills and target role; save. These persist in `local_data/coworkers.sqlite`.
2. In **Daily Tech Brief**, select *Offline article snapshot* and click **Generate my daily top 3**. Show dated article titles, source URLs, personalization and download. Then use *Live RSS* with internet to demonstrate real article titles/dates/URLs.
3. You can mark articles **as read**; the agent saves reading history, prefers unread articles and uses missed interview concepts to adjust future recommendations.
4. In **Career Coach**, click **Find opportunities** to see example or live opportunities. Under **Interactive career coaching session**, choose a topic (such as RAG) and 3 questions, then click **Start a new interactive interview**. Answer each question, review the rubric feedback, and respond to the **adaptive follow-up**. A chat-style transcript and a downloadable session report appear as you go. You can **End early**, or **Resume a saved interview** after refreshing the browser.
5. In **Career Readiness Report**, refresh and show saved answers, average practice score, the number of completed interview sessions, and user action plan. You can also paste a real job/research description and click **Check skill gaps**.

For a **live proof**, internet is required and publisher feeds/job APIs may be unavailable or rate-limited; the app reports that and does not silently substitute sample data.

## 5. How the architecture works

See `docs/architecture.png` and `docs/PROJECT_REPORT.md`.

- Streamlit → FastAPI → LangGraph workflows.
- Agent 1: RSS feeds → rank using student interests and publication date → summarize excerpt → learning brief.
- Agent 2: Remotive jobs or demo fixtures → skill-gap analysis → interview question → rubric evaluation → SQLite memory → readiness report.
- Both: shared profile memory; optional Ollama. LangGraph uses explicit bounded paths rather than autonomous loops.

This version does **not** implement vector RAG. It reuses the workflow and contract style of the earlier consulting project, but the learning agent primarily uses publisher RSS and the coach uses role descriptions and SQLite records. The Career Coach interview adapts follow-up questions to rubric gaps; optional Qwen3 provides additional written feedback, while scores remain deterministic concept-coverage practice indicators. Vector search can be added later if needed.

## 6. Daily scheduling (optional)

Generate and save the daily learning brief on demand:

```powershell
.\.venv\Scripts\python.exe -m scripts.generate_daily --mode sample
```

For live articles:

```powershell
.\.venv\Scripts\python.exe -m scripts.generate_daily --mode live
```

Output is saved under `local_data/`. You may schedule the **live** command once daily using Windows Task Scheduler, with its working directory set to this project root. **No scheduler is installed or started automatically.**

## 7. Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Test coverage includes article ranking, demo labels, skill-gap matching, FastAPI endpoints, saved assessments, **three-turn interviews, adaptive follow-ups, persistence, early ending**, and error handling. Live feeds, the job API and Ollama aren't part of offline tests.

## 8. Files to submit

- `README.md` — commands and walkthrough
- `docs/architecture.png` — workflow/tool/data/memory diagram
- `docs/PROJECT_REPORT.md` — goals, architecture, evaluation and limitations
- `docs/DEMO_CHECKLIST.md` — demonstration script and checklist
- `backend/`, `frontend/`, `scripts/`, `data/` — working prototype and labeled sample fixtures
- `sample_outputs/` — offline article snapshot and fictional career-coaching sample outputs
- `tests/` + `requirements.txt` — reproducibility

The project zip excludes virtual environments, installed models and runtime databases. The assignment didn't specify a mandatory ZIP/report format; check Canvas for any additional submission rules.

## 9. New: interactive coaching API (v2)

A short Windows walkthrough is included at `docs/INTERACTIVE_COACH_QUICK_TEST.md`.

The Career Coach now runs a real multi-turn conversation rather than stopping after the first response. Each turn shows a question, the student's answer, rubric feedback, and a question tailored to a missed concept (or a harder application scenario if concepts are covered). Sessions persist in `local_data/coworkers.sqlite`; you can refresh or restart the app and load an unfinished interview. The default is three questions; the UI supports two to five.

Endpoints:
- `GET /career/interview/topics` — available interview topics.
- `POST /career/interview/start` — body `{"topic":"RAG","max_turns":3}`; returns the current question and session ID.
- `POST /career/interview/{session_id}/answer` — body `{"answer":"..."}`; returns the full updated conversation and next follow-up.
- `GET /career/interview/{session_id}` — load a saved conversation.
- `GET /career/interview/recent` — list recent sessions for resume/review.
- `POST /career/interview/{session_id}/end` — finish early and retain the transcript.

**Testing walkthrough:** Start the backend and Streamlit as above. Open **Career Coach**, choose **RAG**, and start a **3-question** session. For the first answer, enter `Retrieval searches.`. The second question should focus on *grounding*, a missing concept. Answer the follow-up and observe another adaptive question. Complete all three answers, download the transcript, refresh the page, load the saved session, and verify the **Readiness Report** records three answers and one completed interview.

**Honest scope:** The offline follow-ups are targeted by a fixed concept rubric, not full open-ended semantic understanding. Optional Ollama Qwen3 can add qualitative feedback. A strong answer may still score low if it doesn't use the rubric's recognizable wording; do not interpret scores as hiring-readiness predictions. Sessions are for one local user and have no authentication.
