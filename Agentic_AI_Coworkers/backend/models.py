from typing import Literal
from pydantic import BaseModel, Field


class Profile(BaseModel):
    display_name: str = "Student"
    target_role: str = "AI / ML Engineer"
    interests: list[str] = Field(default_factory=lambda: ["agentic AI", "RAG", "cloud", "Python", "machine learning"])
    existing_skills: list[str] = Field(default_factory=lambda: ["Python", "SQL", "FastAPI"])
    weekly_learning_goal: str = "Practice technical concepts for 20 minutes a day"


class Article(BaseModel):
    title: str
    url: str
    source: str
    published_date: str
    excerpt: str
    summary: str = ""
    relevance_reason: str = ""
    reading_minutes: int = 6
    mode: Literal["live_rss", "sample_data"] = "live_rss"


class DailyBrief(BaseModel):
    date: str
    generated_at: str
    mode: Literal["live_rss", "sample_data"]
    note: str
    reading_minutes: int = 18
    profile_role: str
    articles: list[Article]


class Opportunity(BaseModel):
    title: str
    organization: str
    url: str
    published_date: str = ""
    description: str
    location: str = ""
    type: str = "job"
    source: str = "Remotive"
    match_score: int = 0
    mode: Literal["live_api", "sample_data"] = "live_api"


class CoachQuestion(BaseModel):
    question_id: str
    topic: str
    prompt: str
    difficulty: str = "intermediate"
    exercise_type: str = "technical"


class Assessment(BaseModel):
    question_id: str
    question: str
    answer: str
    score: int
    strengths: list[str]
    gaps: list[str]
    feedback: str
    recommended_practice: str
    assessed_at: str
    evaluation_method: str = "transparent_keyword_rubric"


class CareerPreparation(BaseModel):
    goal: str
    opportunities: list[Opportunity]
    opportunities_note: str
    skills_to_build: list[str]
    next_question: CoachQuestion
    next_steps: list[str]


class CareerReport(BaseModel):
    interview_sessions_completed: int = 0
    interview_sessions_in_progress: int = 0
    target_role: str
    existing_skills: list[str]
    attempts: int
    average_score: float | None
    latest_assessments: list[Assessment]
    focus_topics: list[str]
    action_plan: list[str]
    note: str


class RoleAnalysisRequest(BaseModel):
    role_title: str
    description: str = Field(min_length=20)


class InterviewTurn(BaseModel):
    """One completed question/answer/feedback exchange."""
    number: int
    question: CoachQuestion
    assessment: Assessment


class InterviewSession(BaseModel):
    """SQLite-backed, resumable single-user coaching conversation."""
    session_id: str
    target_role: str
    topic: str
    status: Literal["active", "completed", "ended"] = "active"
    max_turns: int = Field(default=3, ge=2, le=5)
    started_at: str
    updated_at: str
    current_question: CoachQuestion | None = None
    current_focus: list[str] = Field(default_factory=list)
    turns: list[InterviewTurn] = Field(default_factory=list)
    final_feedback: str = ""


class InterviewStartRequest(BaseModel):
    topic: str = "auto"
    max_turns: int = Field(default=3, ge=2, le=5)


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=3, max_length=5000)
