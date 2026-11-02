"""A bounded, persistent, multi-turn interview: ask -> answer -> feedback -> follow-up.

Offline mode uses a transparent concept-coverage rubric. With USE_OLLAMA=1,
Qwen supplements written feedback (not the numerical practice score).
"""
from datetime import datetime
from uuid import uuid4
from .models import (
    Profile, CoachQuestion, Assessment, InterviewSession, InterviewTurn,
)
from .coach import QUESTION_BANK, choose_question
from .memory import (
    get_assessments, get_interview_session, save_interview_session, save_assessment,
)
from .llm import generate


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def topics() -> list[str]:
    return [q["topic"] for q in QUESTION_BANK]


def _bank_item(topic: str, profile: Profile):
    if topic.strip().lower() in ("", "auto"):
        selected = choose_question(profile, get_assessments())
        return next(q for q in QUESTION_BANK if q["id"] == selected.question_id)
    return next((q for q in QUESTION_BANK if q["topic"].lower() == topic.strip().lower()), None)


def _initial_question(item: dict) -> CoachQuestion:
    return CoachQuestion(
        question_id=item["id"], topic=item["topic"], prompt=item["prompt"],
        exercise_type=item["type"],
    )


def start_session(profile: Profile, topic: str = "auto", max_turns: int = 3) -> InterviewSession:
    if not 2 <= max_turns <= 5:
        raise ValueError("Number of interview questions must be between 2 and 5")
    bank = _bank_item(topic, profile)
    if bank is None:
        raise ValueError("Unknown topic. Available topics: " + ", ".join(topics()))
    stamp = now()
    session = InterviewSession(
        session_id=str(uuid4()), target_role=profile.target_role,
        topic=bank["topic"], max_turns=max_turns, started_at=stamp,
        updated_at=stamp, current_question=_initial_question(bank),
        current_focus=[name for name, _ in bank["concepts"]],
    )
    save_interview_session(session)
    return session


def _rubric_score(answer: str, item: dict, focus_names: list[str]):
    lower = answer.lower()
    concepts = [(name, needles) for name, needles in item["concepts"] if name in focus_names]
    if not concepts:
        concepts = item["concepts"]
    covered = [name for name, needles in concepts if any(s in lower for s in needles)]
    missed = [name for name, _ in concepts if name not in covered]
    return covered, missed, round(100 * len(covered) / len(concepts))


def _followup_prompt(item: dict, missed: list[str], previous_answer: str, next_turn: int) -> tuple[str, list[str]]:
    """Focus a follow-up on a gap, or ask for an applied trade-off if no gap remains."""
    if missed:
        name = missed[0]
        targeted = {
            "retrieval": "What information would your retriever search, and how would it select useful passages?",
            "grounding": "Explain how retrieved documents become context for the language model, with an example.",
            "citation verification": "How would you check whether a generated claim is really supported by its cited passage?",
            "measurement": "Which measurement or logs would you inspect first, and why?",
            "bottleneck": "How would you isolate whether the bottleneck is in the database or application?",
            "mitigation": "Choose one improvement, and explain how you would verify it helped.",
            "split": "At what point would you split the dataset, and why?",
            "leakage": "Give a concrete example of leakage and how to prevent it.",
            "evaluation metrics": "Which metric would you use on unseen data, and why?",
            "scaling": "How would you design scaling for unpredictable traffic?",
            "reliability": "What happens if a service instance fails? How would you recover?",
            "monitoring": "How would you detect failure before users report it?",
            "dictionary counter": "Which Python data structure would you use to count words?",
            "counting": "Show the counting step for a word that appears three times.",
            "complexity": "What is the time complexity in the number of words, and why?",
            "routing": "How would a manager choose which agent should handle a question?",
            "memory": "Which information would you persist between learning sessions?",
            "verification": "How would you stop an agent from showing an unsupported citation?",
        }
        return (f"Follow-up {next_turn}: Let's focus on **{name}**, which was missing from your answer. "
                + targeted.get(name, f"Explain {name} and give a concrete example."), [name])

    # If all criteria were covered, challenge the learner to apply them to a real situation.
    applications = {
        "RAG": "A search retrieves a very relevant-looking article that doesn't actually support your answer. How would you detect and handle this?",
        "API design": "A slow endpoint improves in testing but becomes slow again in production. How would you diagnose the difference?",
        "ML evaluation": "A model scores 99% in training but poorly on new users. What would you check and change?",
        "Cloud architecture": "Your application is failing during a sudden traffic spike. Which reliability and monitoring steps would you prioritize?",
        "Python coding": "How would you implement word frequency counting efficiently and describe its complexity?",
        "Agentic AI": "A specialist agent provides an answer without valid sources. What should the manager do, and what would you save to memory?",
    }
    text = applications.get(item["topic"], "Give a practical example and explain the trade-offs in your design.")
    return (f"Follow-up {next_turn}: Good coverage of the main concepts. Let's apply them: {text}",
            [name for name, _ in item["concepts"]])


def _session_summary(session: InterviewSession) -> str:
    if not session.turns:
        return "Session ended without an answer. Start a new session whenever you are ready."
    scores = [t.assessment.score for t in session.turns]
    gaps = list(dict.fromkeys(g for turn in session.turns for g in turn.assessment.gaps))
    return (
        f"Interview finished: {len(scores)} answers for {session.topic}. "
        f"Average keyword-rubric practice score: {sum(scores) / len(scores):.0f}/100. "
        + (f"Review these concepts: {', '.join(gaps)}. " if gaps else "All checked rubric concepts were mentioned. ")
        + "Scores measure concept mentions, not overall answer correctness. "
        + "Check the Career Readiness Report for saved practice and next steps."
    )


def answer_session(session_id: str, answer: str) -> InterviewSession:
    session = get_interview_session(session_id)
    if session is None:
        raise LookupError("Interview session not found")
    if session.status != "active" or session.current_question is None:
        raise ValueError("This interview has finished. Start a new session to continue practicing.")
    answer = answer.strip()
    if len(answer) < 3:
        raise ValueError("Please enter a meaningful answer")
    if len(answer) > 5000:
        raise ValueError("Answer cannot exceed 5000 characters")

    bank = next(q for q in QUESTION_BANK if q["topic"] == session.topic)
    question = session.current_question
    covered, missed, score = _rubric_score(answer, bank, session.current_focus)
    rubric = (
        f"Practice concept-coverage score: {score}/100. "
        + ("You mentioned: " + ", ".join(covered) + ". " if covered else "The key concepts were not clearly mentioned. ")
        + ("Try adding: " + ", ".join(missed) + "." if missed else "Nice coverage; an example or trade-off could strengthen your answer.")
    )
    llm_feedback = generate(
        f"Target role: {session.target_role}\nTopic: {session.topic}\nQuestion: {question.prompt}\n"
        f"Student answer: {answer[:2500]}\nRecognized rubric concepts: {covered}\n"
        f"Missing concepts: {missed}\nGive 2 short specific coaching sentences. "
        "Do not change the score or pretend you tested code.",
        "You are an encouraging, technically accurate interview coach. Evaluate only the supplied answer and admit uncertainty.",
        160,
    )
    if llm_feedback:
        rubric += " Additional AI coaching: " + llm_feedback
    assessed = Assessment(
        question_id=question.question_id, question=question.prompt,
        answer=answer, score=score, strengths=covered, gaps=missed,
        feedback=rubric, recommended_practice=bank["practice"],
        assessed_at=now(),
        evaluation_method="keyword_concept_coverage_with_optional_llm_feedback",
    )
    number = len(session.turns) + 1
    session.turns.append(InterviewTurn(number=number, question=question, assessment=assessed))
    save_assessment(assessed)
    if number >= session.max_turns:
        session.status = "completed"
        session.current_question = None
        session.current_focus = []
        session.final_feedback = _session_summary(session)
    else:
        prompt, focus = _followup_prompt(bank, missed, answer, number + 1)
        session.current_question = CoachQuestion(
            question_id=f"{bank['id']}-followup-{number + 1}",
            topic=bank["topic"], prompt=prompt,
            difficulty="follow-up", exercise_type=bank["type"],
        )
        session.current_focus = focus
    session.updated_at = now()
    save_interview_session(session)
    return session


def end_session(session_id: str) -> InterviewSession:
    session = get_interview_session(session_id)
    if session is None:
        raise LookupError("Interview session not found")
    if session.status == "active":
        session.status = "ended"
        session.current_question = None
        session.current_focus = []
        session.final_feedback = _session_summary(session)
        session.updated_at = now()
        save_interview_session(session)
    return session
