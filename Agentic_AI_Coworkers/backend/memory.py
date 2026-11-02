"""Simple local memory. One-user academic prototype; no authentication."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .models import Profile, DailyBrief, Assessment


def db_file() -> Path:
    path = Path(os.getenv("COWORKER_DB", "local_data/coworkers.sqlite"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def conn():
    db = sqlite3.connect(db_file())
    try:
        db.execute("CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS briefs (date TEXT NOT NULL, mode TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(date,mode))")
        db.execute("CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS read_articles (url TEXT PRIMARY KEY, title TEXT, marked_at TEXT NOT NULL)")
        db.commit()
        yield db
        db.commit()
    finally:
        db.close()


def get_profile() -> Profile:
    with conn() as db:
        row = db.execute("SELECT payload FROM profile WHERE id=1").fetchone()
    return Profile.model_validate_json(row[0]) if row else Profile()


def save_profile(profile: Profile) -> Profile:
    with conn() as db:
        db.execute("INSERT OR REPLACE INTO profile(id,payload) VALUES(1,?)", (profile.model_dump_json(),))
    return profile


def save_brief(brief: DailyBrief):
    with conn() as db:
        db.execute("INSERT OR REPLACE INTO briefs(date,mode,payload) VALUES(?,?,?)", (brief.date, brief.mode, brief.model_dump_json()))


def get_brief(date: str, mode: str) -> DailyBrief | None:
    with conn() as db:
        row = db.execute("SELECT payload FROM briefs WHERE date=? AND mode=?", (date, mode)).fetchone()
    return DailyBrief.model_validate_json(row[0]) if row else None


def save_assessment(assessment: Assessment):
    with conn() as db:
        db.execute("INSERT INTO assessments(payload) VALUES(?)", (assessment.model_dump_json(),))


def get_assessments(limit: int = 100) -> list[Assessment]:
    with conn() as db:
        rows = db.execute("SELECT payload FROM assessments ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [Assessment.model_validate_json(r[0]) for r in rows]


def mark_article_read(url: str, title: str):
    from datetime import datetime
    with conn() as db:
        db.execute("INSERT OR REPLACE INTO read_articles(url,title,marked_at) VALUES(?,?,?)",
                   (url, title, datetime.now().astimezone().isoformat(timespec="seconds")))


def reading_history() -> list[dict]:
    with conn() as db:
        rows = db.execute("SELECT url,title,marked_at FROM read_articles ORDER BY marked_at DESC").fetchall()
    return [{"url": r[0], "title": r[1], "marked_at": r[2]} for r in rows]


def save_interview_session(session):
    """Persist every turn, so a page refresh does not lose the conversation."""
    with conn() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS interview_sessions "
            "(id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        db.execute(
            "INSERT OR REPLACE INTO interview_sessions(id,updated_at,payload) VALUES (?,?,?)",
            (session.session_id, session.updated_at, session.model_dump_json()),
        )


def get_interview_session(session_id: str):
    from .models import InterviewSession
    with conn() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS interview_sessions "
            "(id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        row = db.execute(
            "SELECT payload FROM interview_sessions WHERE id=?", (session_id,)
        ).fetchone()
    return InterviewSession.model_validate_json(row[0]) if row else None


def list_interview_sessions(limit: int = 10):
    from .models import InterviewSession
    with conn() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS interview_sessions "
            "(id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        rows = db.execute(
            "SELECT payload FROM interview_sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [InterviewSession.model_validate_json(row[0]) for row in rows]
