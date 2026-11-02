"""FastAPI entrypoint. Run: python -m uvicorn backend.main:app --reload --port 8001"""
from datetime import datetime
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .models import (Profile, DailyBrief, Assessment, CareerPreparation, CareerReport,
                     RoleAnalysisRequest, InterviewStartRequest, InterviewAnswerRequest, InterviewSession)
from .memory import get_profile, save_profile, save_brief, mark_article_read, reading_history
from .workflows import DAILY_GRAPH, CAREER_GRAPH
from .coach import evaluate, career_report, analyze_role
from .interview import start_session, answer_session, end_session, topics
from .memory import get_interview_session, list_interview_sessions

app = FastAPI(title="Personal Agentic AI Coworkers", version="0.1.0")


class RunOptions(BaseModel):
    mode: Literal["live", "sample"] = "sample"


class AnswerRequest(BaseModel):
    question_id: str
    answer: str = Field(min_length=3)


@app.get("/health")
def health():
    return {"status": "ok", "agents": ["DailyTechUpgradeAgent", "nextLevelPersonalCoachForCareerLevel"]}


@app.get("/profile", response_model=Profile)
def profile_get():
    return get_profile()


@app.put("/profile", response_model=Profile)
def profile_put(profile: Profile):
    return save_profile(profile)


@app.post("/daily-brief", response_model=DailyBrief)
def daily_brief(options: RunOptions):
    profile = get_profile()
    mode = "sample_data" if options.mode == "sample" else "live_rss"
    try:
        result = DAILY_GRAPH.invoke({"profile": profile, "mode": mode})["brief"]
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    save_brief(result)
    return result


@app.post("/career/prepare", response_model=CareerPreparation)
def career_prepare(options: RunOptions):
    mode = "sample_data" if options.mode == "sample" else "live_api"
    return CAREER_GRAPH.invoke({"profile": get_profile(), "mode": mode})["preparation"]


@app.post("/career/answer", response_model=Assessment)
def career_answer(answer: AnswerRequest):
    try:
        return evaluate(answer.question_id, answer.answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/career/interview/topics")
def interview_topics():
    return {"topics": topics()}


@app.post("/career/interview/start", response_model=InterviewSession)
def interview_start(options: InterviewStartRequest):
    try:
        return start_session(get_profile(), options.topic, options.max_turns)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/career/interview/recent", response_model=list[InterviewSession])
def interview_recent():
    return list_interview_sessions(limit=10)


@app.get("/career/interview/{session_id}", response_model=InterviewSession)
def interview_get(session_id: str):
    session = get_interview_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


@app.post("/career/interview/{session_id}/answer", response_model=InterviewSession)
def interview_reply(session_id: str, submission: InterviewAnswerRequest):
    try:
        return answer_session(session_id, submission.answer)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/career/interview/{session_id}/end", response_model=InterviewSession)
def interview_end(session_id: str):
    try:
        return end_session(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/career/analyze-role")
def career_analyze_role(role: RoleAnalysisRequest):
    return {"role_title": role.role_title, **analyze_role(role.description, get_profile())}


@app.get("/career/report", response_model=CareerReport)
def report():
    return career_report(get_profile())


class ReadArticle(BaseModel):
    url: str = Field(min_length=10)
    title: str = Field(min_length=2)


@app.post("/reading/mark-read")
def read_article(item: ReadArticle):
    # Only mark the user's own reading; this does not fetch the given URL.
    mark_article_read(item.url, item.title)
    return {"saved": True}


@app.get("/reading/history")
def reading_progress():
    return {"count": len(reading_history()), "articles": reading_history()}
