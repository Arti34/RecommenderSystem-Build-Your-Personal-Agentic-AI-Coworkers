"""Career Coach: opportunities, skill-gap assessment and interactive interviews."""
import json
import re
from datetime import datetime
from pathlib import Path
import requests
from .articles import clean_html
from .models import (Profile, Opportunity, CoachQuestion, Assessment,
                     CareerReport)
from .memory import get_assessments, save_assessment, list_interview_sessions
from .llm import generate

SKILLS = ["python", "sql", "machine learning", "rag", "llm", "langgraph", "api", "fastapi",
          "aws", "cloud", "docker", "git", "statistics", "pytorch", "communication", "system design"]

QUESTION_BANK = [
    {"id": "rag-01", "topic": "RAG", "type": "technical",
     "prompt": "Explain retrieval-augmented generation (RAG). Why is retrieval useful, and how would you check source citations?",
     "concepts": [("retrieval", ["retriev", "search"]), ("grounding", ["context", "document", "source"]),
                  ("citation verification", ["citat", "evidence", "support"])],
     "practice": "Explain retrieval -> context -> model -> source verification using a short diagram."},
    {"id": "api-01", "topic": "API design", "type": "technical",
     "prompt": "An API endpoint becomes slow under high request volume. Name three steps you would take to investigate and improve it.",
     "concepts": [("measurement", ["metric", "profil", "log", "monitor"]),
                  ("bottleneck", ["bottleneck", "database", "query", "latency"]),
                  ("mitigation", ["cache", "index", "scale", "queue", "optimiz"])],
     "practice": "Describe an experiment with latency before/after one optimization."},
    {"id": "ml-01", "topic": "ML evaluation", "type": "technical",
     "prompt": "How do you avoid data leakage in machine learning, and how do you measure model performance on unseen data?",
     "concepts": [("split", ["train", "test", "valid"]),
                  ("leakage", ["leak", "future", "target"]),
                  ("evaluation metrics", ["metric", "accuracy", "precision", "recall", "f1", "mae"])],
     "practice": "Create a toy train/test split and explain what information must be kept out of training."},
    {"id": "cloud-01", "topic": "Cloud architecture", "type": "scenario",
     "prompt": "Your AWS service experiences occasional traffic spikes. How could you design for scaling, reliability and monitoring?",
     "concepts": [("scaling", ["scal", "autoscal", "load balanc"]),
                  ("reliability", ["availability", "redundan", "retry", "failover"]),
                  ("monitoring", ["monitor", "metric", "cloudwatch", "alert"])],
     "practice": "Sketch a load-balanced service with monitoring and one recovery mechanism."},
    {"id": "code-01", "topic": "Python coding", "type": "coding",
     "prompt": "Write or explain a Python approach to count the frequency of each word in a list. Discuss time complexity.",
     "concepts": [("dictionary counter", ["dict", "counter", "hash"]),
                  ("counting", ["count", "frequen", "+=", "get("]),
                  ("complexity", ["o(n)", "linear", "complexity"])],
     "practice": "Implement with collections.Counter and test empty and repeated inputs."},
    {"id": "agent-01", "topic": "Agentic AI", "type": "scenario",
     "prompt": "Design a two-agent assistant that reads technical articles and quizzes a learner. What tools, memory and safety checks are needed?",
     "concepts": [("routing", ["rout", "workflow", "orchestrat"]),
                  ("memory", ["memory", "database", "persist", "history"]),
                  ("verification", ["verif", "citation", "source", "validat"])],
     "practice": "Draw an agent flow including the user, tools, storage and verification stage."},
]


def choose_question(profile: Profile, attempts: list[Assessment]) -> CoachQuestion:
    used = [a.question_id for a in attempts]
    # Prefer untried questions, with repeat after the six-question cycle.
    q = next((x for x in QUESTION_BANK if x["id"] not in used), QUESTION_BANK[len(attempts) % len(QUESTION_BANK)])
    return CoachQuestion(question_id=q["id"], topic=q["topic"], prompt=q["prompt"],
                         exercise_type=q["type"])


def evaluate(question_id: str, answer: str) -> Assessment:
    q = next((x for x in QUESTION_BANK if x["id"] == question_id), None)
    if q is None:
        raise ValueError("Unknown question ID")
    if len(answer.strip()) < 3:
        raise ValueError("Please submit a meaningful answer")
    lower = answer.lower()
    strengths = [name for name, needles in q["concepts"] if any(n in lower for n in needles)]
    gaps = [name for name, needles in q["concepts"] if name not in strengths]
    score = round(100 * len(strengths) / len(q["concepts"]))
    feedback = (
        f"Rubric-based practice score: {score}/100. "
        + ("You mentioned: " + ", ".join(strengths) + ". " if strengths else "Your answer did not mention the rubric concepts clearly. ")
        + ("Add: " + ", ".join(gaps) + "." if gaps else "You covered all listed concepts; explain trade-offs and give an example next.")
    )
    ai = generate(
        f"Question: {q['prompt']}\nStudent answer: {answer[:2400]}\nRubric concepts covered: {strengths}\nMissing concepts: {gaps}\nGive 2 helpful sentences of constructive feedback, no numeric score.",
        "You are a career coach. Critique only the actual answer; do not invent the student's skills. The externally calculated rubric score is fixed.",
        160,
    )
    if ai:
        feedback += " Local LLM feedback: " + ai
    assessment = Assessment(
        question_id=question_id, question=q["prompt"], answer=answer,
        score=score, strengths=strengths, gaps=gaps, feedback=feedback,
        recommended_practice=q["practice"], assessed_at=datetime.now().astimezone().isoformat(timespec="seconds"),
    )
    save_assessment(assessment)
    return assessment


def matching_skills(text: str) -> list[str]:
    text = text.lower()
    # Simple disclosed keyword matching, not a hiring-eligibility classifier.
    return [skill for skill in SKILLS if re.search(r"(?<![a-z])" + re.escape(skill) + r"(?![a-z])", text)]


def analyze_role(description: str, profile: Profile) -> dict:
    requested = matching_skills(description)
    known = " ".join(profile.existing_skills).lower()
    matching = [s for s in requested if s in known]
    missing = [s for s in requested if s not in known]
    return {
        "required_skills_mentioned": requested,
        "skills_matching_profile": matching,
        "skills_to_explore": missing,
        "readiness_note": "Keyword-based learning-gap estimate, not a hiring prediction or formal qualification assessment."
    }


def sample_opportunities() -> list[Opportunity]:
    path = Path(__file__).resolve().parent.parent / "data" / "sample_opportunities.json"
    return [Opportunity(**row, mode="sample_data") for row in json.loads(path.read_text(encoding="utf-8"))]


def live_opportunities(profile: Profile) -> tuple[list[Opportunity], str]:
    # Documented Remotive API, live remote job listings; not internship/research coverage.
    query = "machine learning" if any(x in profile.target_role.lower() for x in ("ml", "ai", "data")) else "software"
    try:
        response = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": query, "limit": 30},
            headers={"User-Agent": "Student-CareerCoach-Demo/1.0"}, timeout=12,
        )
        response.raise_for_status()
        data = response.json()
        entries = data.get("jobs", [])
        result = []
        for job in entries:
            desc = clean_html(job.get("description", ""))
            link = job.get("url", "")
            if not link.startswith("https://remotive.com/"):
                continue
            requested = matching_skills(desc)
            known = " ".join(profile.existing_skills).lower()
            score = round(100 * len([s for s in requested if s in known]) / len(requested)) if requested else 0
            result.append(Opportunity(
                title=job.get("title", "Untitled"), organization=job.get("company_name", "Not listed"),
                url=link, published_date=job.get("publication_date", ""),
                description=desc[:1400], location=job.get("candidate_required_location", "Remote"),
                type=job.get("job_type", "job") or "job", source="Remotive (live jobs API)", match_score=score,
            ))
        return sorted(result, key=lambda j: j.match_score, reverse=True)[:5], (
            "LIVE: Remote job listings from Remotive; may be delayed and have eligibility/location restrictions. "
            "Always confirm current availability. Research and startup opportunities require additional sources or pasted descriptions."
        )
    except (requests.RequestException, ValueError, TypeError):
        return [], "Live jobs unavailable. Check internet access or use explicitly labeled sample mode."


def career_report(profile: Profile) -> CareerReport:
    attempts = get_assessments()
    sessions = list_interview_sessions(limit=1000)
    missed = []
    for a in attempts[:6]:
        missed.extend(a.gaps)
    focus = list(dict.fromkeys(missed))[:5]
    score = round(sum(a.score for a in attempts) / len(attempts), 1) if attempts else None
    return CareerReport(
        interview_sessions_completed=sum(s.status == "completed" for s in sessions),
        interview_sessions_in_progress=sum(s.status == "active" for s in sessions),
        target_role=profile.target_role, existing_skills=profile.existing_skills,
        attempts=len(attempts), average_score=score, latest_assessments=attempts[:5],
        focus_topics=focus, action_plan=[
            "Practice one 10-minute technical answer or coding exercise every day.",
            "Review missed rubric concepts and retry the question after studying.",
            "Compare a real job description with your skill profile and build one small portfolio project.",
        ],
        note="Scores reflect explicit keyword-rubric coverage, not a formal interview assessment. No employment outcome is predicted.",
    )
