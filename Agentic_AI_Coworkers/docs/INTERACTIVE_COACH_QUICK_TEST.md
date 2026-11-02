# Interactive Career Coach — Windows Quick Test

The Career Coach is now a multi-turn conversation. Questions adapt to the concepts you missed in the previous answer, and the session transcript is stored in SQLite.

## Run it

1. Extract the ZIP and open the **Agentic_AI_Coworkers** folder.
2. Double-click `setup_windows.bat` once (requires internet for packages).
3. Double-click `start_backend.bat` and keep it open.
4. Double-click `start_frontend.bat` and keep it open.
5. Open http://localhost:8502 and choose the **Career Coach** tab.
6. Under **Interactive career coaching session**, choose `RAG`, then `3 questions`, then select **Start a new interactive interview**.
7. For question 1, answer `Retrieval searches.` and click **Send answer and get follow-up**.
8. The coach should give feedback about missing concepts and ask a follow-up about **grounding**.
9. Answer `Retrieved documents are passed as context to the language model.`. It should then focus on **citation verification**.
10. Finish question 3 with `Check each cited claim against its source passage and flag unsupported statements.`
11. The interview should finish with a summary. Download the transcript.
12. Refresh the browser, choose **Resume or review a saved interview**, and load it again to verify persistence.
13. Open **Readiness Report**, click Refresh, and check three saved practice answers and one completed interview.

## Optional Ollama mode

Use `start_backend_with_ollama.bat` **instead of** `start_backend.bat` to add local Qwen3 coaching comments. First start Ollama and download `qwen3:1.7b`. The offline version does not require Ollama.

## Automated checks

Run from the project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected test count: **7 passing tests**. Tests include a multi-turn conversation, follow-up selection, persistence, early termination and invalid session handling. Install the real dependencies before running these tests on your computer.

## Interpretation and limitations

This is a classroom prototype with a fixed concept keyword rubric. It checks coverage of terms; it **does not reliably judge factual correctness**. The follow-up is adaptive based on missed rubric concepts, not a free-form reasoning agent. With Ollama enabled, the program adds generative coaching comments, but scores stay rubric-based. The SQLite database is local, single-user, and has no authentication.
