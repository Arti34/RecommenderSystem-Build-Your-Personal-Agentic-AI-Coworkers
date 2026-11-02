"""Two explicit LangGraph agent workflows; no unbounded autonomous loops."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .models import Profile, DailyBrief, Opportunity, CareerPreparation, CoachQuestion
from .articles import fetch_live_articles, load_sample_articles, compose_brief
from .coach import live_opportunities, sample_opportunities, choose_question, analyze_role
from .memory import get_assessments, reading_history


class LearningState(TypedDict, total=False):
    profile: Profile
    mode: str
    discovered: list
    brief: DailyBrief


def article_discovery(state: LearningState):
    data = load_sample_articles() if state["mode"] == "sample_data" else fetch_live_articles()
    return {"discovered": data}


def article_rank_and_brief(state: LearningState):
    profile = state["profile"].model_copy(deep=True)
    # Use recurring interview gaps as an additional learning-interest signal.
    for assessment in get_assessments(limit=3):
        for missing in assessment.gaps:
            if missing not in profile.interests:
                profile.interests.append(missing)
    read_urls = {row["url"] for row in reading_history()}
    brief = compose_brief(state["discovered"], profile, state["mode"], read_urls)
    return {"brief": brief}


article_flow = StateGraph(LearningState)
article_flow.add_node("discover_authoritative_feeds", article_discovery)
article_flow.add_node("rank_and_summarize_top_three", article_rank_and_brief)
article_flow.add_edge(START, "discover_authoritative_feeds")
article_flow.add_edge("discover_authoritative_feeds", "rank_and_summarize_top_three")
article_flow.add_edge("rank_and_summarize_top_three", END)
DAILY_GRAPH = article_flow.compile()


class CareerState(TypedDict, total=False):
    profile: Profile
    mode: str
    opportunities: list[Opportunity]
    opportunities_note: str
    skills_to_build: list[str]
    next_question: CoachQuestion
    preparation: CareerPreparation


def discover_opportunities(state: CareerState):
    if state["mode"] == "sample_data":
        opportunities, note = sample_opportunities(), "DEMO: fictional jobs/research/startup examples. These are not current openings."
    else:
        opportunities, note = live_opportunities(state["profile"])
    return {"opportunities": opportunities, "opportunities_note": note}


def assess_skills_and_question(state: CareerState):
    profile = state["profile"]
    gaps = []
    for opportunity in state["opportunities"][:3]:
        gaps += analyze_role(opportunity.description, profile)["skills_to_explore"]
    return {"skills_to_build": list(dict.fromkeys(gaps))[:6],
            "next_question": choose_question(profile, get_assessments())}


def prepare_career_report(state: CareerState):
    return {"preparation": CareerPreparation(
        goal=state["profile"].target_role, opportunities=state["opportunities"],
        opportunities_note=state["opportunities_note"],
        skills_to_build=state["skills_to_build"], next_question=state["next_question"],
        next_steps=["Read two role descriptions and verify location/eligibility.",
                    "Answer the interview question and review the feedback.",
                    "Save a learning goal and return after another practice session."],
    )}


career_flow = StateGraph(CareerState)
career_flow.add_node("find_opportunities", discover_opportunities)
career_flow.add_node("analyze_skill_gaps_and_choose_question", assess_skills_and_question)
career_flow.add_node("compile_career_preparation", prepare_career_report)
career_flow.add_edge(START, "find_opportunities")
career_flow.add_edge("find_opportunities", "analyze_skill_gaps_and_choose_question")
career_flow.add_edge("analyze_skill_gaps_and_choose_question", "compile_career_preparation")
career_flow.add_edge("compile_career_preparation", END)
CAREER_GRAPH = career_flow.compile()
