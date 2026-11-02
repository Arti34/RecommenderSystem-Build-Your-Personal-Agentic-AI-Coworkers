"""Streamlit UI for a local FastAPI server."""
import json
import os
import requests
import streamlit as st

st.set_page_config(page_title="My AI Coworkers", page_icon="🎓", layout="wide")


def api(method: str, path: str, **kwargs):
    base = st.session_state.get("backend_url", "http://127.0.0.1:8001").rstrip("/")
    try:
        response = requests.request(method, base + path, timeout=180, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise ValueError(f"Backend error ({response.status_code}): {detail}")
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        st.error(str(exc))
        return None


@st.cache_data(ttl=20, show_spinner=False)
def initial_profile(base):
    response = requests.get(base.rstrip("/") + "/profile", timeout=5)
    response.raise_for_status()
    return response.json()


st.sidebar.title("⚙️ Local setup")
st.session_state.backend_url = st.sidebar.text_input("FastAPI URL", value="http://127.0.0.1:8001")
try:
    profile = initial_profile(st.session_state.backend_url)
except Exception:
    st.error("Could not reach FastAPI. Start the backend first using the README instructions.")
    st.stop()

st.sidebar.caption("This is a single-user learning prototype. Profile and practice answers are saved locally in SQLite.")
st.title("🎓 My Agentic AI Coworkers")
st.caption("Two LangGraph coworkers | Local profile memory | Streamlit + FastAPI | Optional Ollama Qwen3")

tab_articles, tab_career, tab_progress, tab_profile = st.tabs([
    "📚 Daily Tech Brief", "🚀 Career Coach", "📊 Readiness Report", "👤 My Profile"
])

with tab_articles:
    st.subheader("DailyTechUpgradeAgent")
    st.write("Discover the top three technical readings for an 18-minute session, personalized to your interests.")
    article_mode = st.radio("Source mode", ["Offline article snapshot", "Live RSS (internet required)"], horizontal=True,
                            help="Offline snapshot uses published October 2026 articles, not today's feed. Live mode fetches current RSS with dates and links.")
    if st.button("Generate my daily top 3", type="primary"):
        with st.spinner("Finding articles and preparing your brief..."):
            brief = api("POST", "/daily-brief", json={"mode": "sample" if article_mode.startswith("Offline") else "live"})
        if brief:
            st.session_state.brief = brief
    if st.session_state.get("brief"):
        brief = st.session_state.brief
        if brief["mode"] == "sample_data":
            st.warning(brief["note"])
        else:
            st.info(brief["note"])
        st.write(f"**Date:** {brief['date']}  |  **Reading goal:** {brief['reading_minutes']} minutes  |  **Career focus:** {brief['profile_role']}")
        output = [f"# Daily Technical Learning Brief — {brief['date']}", "", brief["note"], ""]
        for i, item in enumerate(brief["articles"], 1):
            st.markdown(f"### {i}. {item['title']}")
            st.caption(f"{item['source']} · {item['published_date']} · {item['reading_minutes']} minute reading slot")
            st.markdown(f"[Read original article]({item['url']})")
            st.write(item["summary"])
            st.markdown(f"**Why it matters for you:** {item['relevance_reason']}")
            if st.button(f"Mark article {i} as read", key="read_" + item["url"]):
                if api("POST", "/reading/mark-read", json={"url": item["url"], "title": item["title"]}):
                    st.success("Saved to your reading history. Future recommendations will favor unread sources.")
            output += [f"## {i}. {item['title']}", f"Source: {item['source']} | Date: {item['published_date']}",
                       f"URL: {item['url']}", item["summary"], f"Learning value: {item['relevance_reason']}", ""]
        st.download_button("Download today's brief (.md)", data="\n".join(output), file_name="daily_tech_brief.md")

with tab_career:
    st.subheader("nextLevelPersonalCoachForCareerLevel")
    st.write("Explore career opportunities, then practice in a **multi-turn interactive interview**. "
             "The coach reviews each answer and adapts the next question to missing concepts.")

    st.markdown("### 1. Explore opportunities")
    career_mode = st.radio("Opportunity mode", ["Sample demo (offline)", "Live jobs (Remotive API)"], horizontal=True)
    if st.button("Find opportunities"):
        with st.spinner("Preparing your career opportunities..."):
            prep = api("POST", "/career/prepare", json={"mode": "sample" if career_mode.startswith("Sample") else "live"})
        if prep:
            st.session_state.prep = prep
    if st.session_state.get("prep"):
        prep = st.session_state.prep
        st.info(prep["opportunities_note"])
        st.markdown(f"**Career goal:** {prep['goal']}")
        if prep["skills_to_build"]:
            st.write("**Potential skills to build:** " + ", ".join(prep["skills_to_build"]))
        for item in prep["opportunities"]:
            with st.expander(f"{item['title']} · {item['organization']}"):
                st.caption(f"{item['source']} | {item['location']} | {item['published_date']} | keyword match {item['match_score']}%")
                st.write(item["description"][:650])
                st.markdown(f"[View listing]({item['url']})")
        if not prep["opportunities"]:
            st.warning("No live jobs returned. Try demo mode or paste an opportunity below.")

    st.divider()
    st.markdown("### 2. Interactive career coaching session")
    st.caption("Choose a topic, answer 2–5 questions, receive feedback after each answer, and get adaptive follow-ups. "
               "Sessions are saved in local SQLite and can be resumed. Scores are simple concept-coverage indicators.")
    topics_result = api("GET", "/career/interview/topics")
    available_topics = ["auto"] + (topics_result["topics"] if topics_result else [])
    c_topic, c_rounds = st.columns([2, 1])
    with c_topic:
        chosen_topic = st.selectbox("Interview topic", available_topics, format_func=lambda t: "Personalized / next topic" if t == "auto" else t)
    with c_rounds:
        chosen_rounds = st.selectbox("Questions per session", [2, 3, 4, 5], index=1)
    if st.button("Start a new interactive interview", type="primary"):
        result = api("POST", "/career/interview/start", json={"topic": chosen_topic, "max_turns": chosen_rounds})
        if result:
            st.session_state.coach_session = result
            st.rerun()

    recent = api("GET", "/career/interview/recent") or []
    if recent:
        options = ["Select a saved interview"] + [r["session_id"] for r in recent]
        labels = {r["session_id"]: f"{r['topic']} · {len(r['turns'])}/{r['max_turns']} answers · {r['status']} · {r['started_at'][:16]}" for r in recent}
        selected = st.selectbox("Resume or review a saved interview", options,
                                format_func=lambda x: labels.get(x, x))
        if st.button("Load saved interview", disabled=selected == options[0]):
            result = api("GET", f"/career/interview/{selected}")
            if result:
                st.session_state.coach_session = result
                st.rerun()

    session = st.session_state.get("coach_session")
    if session:
        st.markdown(f"**Interview topic:** {session['topic']}  |  **Target role:** {session['target_role']}  |  "
                    f"**Progress:** {len(session['turns'])}/{session['max_turns']} answers  |  "
                    f"**Status:** {session['status']}")
        st.progress(len(session["turns"]) / session["max_turns"])
        with st.chat_message("assistant"):
            st.write("Welcome! I will ask a question, review your answer and ask a follow-up based on your response. "
                     "You can finish early or resume later.")
        for turn in session["turns"]:
            with st.chat_message("assistant"):
                st.markdown(f"**Question {turn['number']} · {turn['question']['topic']}**")
                st.write(turn["question"]["prompt"])
            with st.chat_message("user"):
                st.write(turn["assessment"]["answer"])
            with st.chat_message("assistant"):
                a = turn["assessment"]
                st.markdown(f"**Coach feedback · practice score {a['score']}/100**")
                st.write(a["feedback"])
                st.write("**Practice idea:** " + a["recommended_practice"])

        if session["status"] == "active" and session["current_question"]:
            q = session["current_question"]
            with st.chat_message("assistant"):
                st.markdown(f"**Question {len(session['turns']) + 1} · {q['topic']}**")
                st.write(q["prompt"])
            with st.form("interactive_interview_answer", clear_on_submit=True):
                response_text = st.text_area("Your answer", height=145,
                                             placeholder="Type your answer in your own words. You can include code or an example.")
                sent = st.form_submit_button("Send answer and get follow-up")
            if sent:
                if len(response_text.strip()) < 3:
                    st.warning("Please type an answer before submitting.")
                else:
                    with st.spinner("Evaluating your answer and preparing the next question..."):
                        updated = api("POST", f"/career/interview/{session['session_id']}/answer",
                                      json={"answer": response_text})
                    if updated:
                        st.session_state.coach_session = updated
                        st.rerun()
            if st.button("End this interview early"):
                updated = api("POST", f"/career/interview/{session['session_id']}/end")
                if updated:
                    st.session_state.coach_session = updated
                    st.rerun()
        else:
            st.success(session.get("final_feedback") or "Interview finished.")
            st.info("Open **Readiness Report** to see your saved learning gaps and action plan.")

        transcript = [f"# Interactive Career Coaching Session — {session['topic']}",
                      f"Target role: {session['target_role']}", f"Status: {session['status']}", ""]
        for t in session["turns"]:
            transcript += [f"## Question {t['number']}", t["question"]["prompt"], "",
                           "### My answer", t["assessment"]["answer"], "",
                           "### Coach feedback", t["assessment"]["feedback"], "",
                           f"Practice next: {t['assessment']['recommended_practice']}", ""]
        transcript.append(session.get("final_feedback", ""))
        st.download_button("Download interview transcript (.md)", data="\n".join(transcript),
                           file_name="interactive_career_coaching_session.md",
                           key="download_interview_transcript")

    st.divider()
    st.markdown("### 3. Analyze any opportunity description")
    st.write("Paste a real internship, research, job, or startup opportunity description to compare it with your listed skills.")
    with st.form("role_form"):
        role_title = st.text_input("Opportunity title", value="AI Engineer")
        role_text = st.text_area("Role description / requirements", height=125,
                                 placeholder="Paste at least 20 characters of a real opportunity description...")
        analyze = st.form_submit_button("Check skill gaps")
    if analyze:
        result = api("POST", "/career/analyze-role", json={"role_title": role_title, "description": role_text})
        if result:
            st.json(result)

with tab_progress:
    st.subheader("Career Readiness Report")
    history = api("GET", "/reading/history")
    if history:
        st.metric("Articles marked as read", history["count"])
    if st.button("Refresh my progress") or "report" not in st.session_state:
        result = api("GET", "/career/report")
        if result:
            st.session_state.report = result
    if st.session_state.get("report"):
        r = st.session_state.report
        c1, c2, c3 = st.columns(3)
        c1.metric("Practice answers saved", r["attempts"])
        c2.metric("Completed interviews", r.get("interview_sessions_completed", 0))
        c3.metric("Average practice rubric", "Not yet assessed" if r["average_score"] is None else f"{r['average_score']} / 100")
        st.write("**Goal:** " + r["target_role"])
        st.write("**Focus areas:** " + (", ".join(r["focus_topics"]) if r["focus_topics"] else "Complete your first interview question"))
        for a in r["latest_assessments"]:
            with st.expander(f"{a['question_id']} · {a['score']}/100 · {a['assessed_at']}"):
                st.write(a["question"])
                st.write("**Your answer:** " + a["answer"])
                st.write(a["feedback"])
        st.write("**Recommended next actions**")
        for action in r["action_plan"]:
            st.markdown(f"- {action}")
        st.caption(r["note"])
        md = "# Career Readiness Report\n\n" + f"Target role: {r['target_role']}\nAttempts: {r['attempts']}\nAverage score: {r['average_score']}\n\n"
        md += "## Focus topics\n" + "\n".join("- " + x for x in r["focus_topics"]) + "\n\n## Action plan\n"
        md += "\n".join("- " + x for x in r["action_plan"]) + "\n\n## Recent assessments\n"
        for a in r["latest_assessments"]:
            md += (f"\n### {a['question_id']} — {a['score']}/100\n"
                   f"Question: {a['question']}\n\nAnswer: {a['answer']}\n\n"
                   f"Feedback: {a['feedback']}\n\nPractice: {a['recommended_practice']}\n")
        md += "\n" + r["note"] + "\n"
        st.download_button("Download career report (.md)", data=md, file_name="career_readiness_report.md")

with tab_profile:
    st.subheader("Personalization and local memory")
    with st.form("profile_form"):
        name = st.text_input("Display name", value=profile["display_name"])
        role = st.text_input("Next role or career direction", value=profile["target_role"])
        interests = st.text_area("Technical interests (comma separated)", value=", ".join(profile["interests"]))
        skills = st.text_area("Skills you already know (comma separated)", value=", ".join(profile["existing_skills"]))
        goal = st.text_input("Weekly learning goal", value=profile["weekly_learning_goal"])
        save = st.form_submit_button("Save my profile")
    if save:
        payload = {
            "display_name": name, "target_role": role,
            "interests": [x.strip() for x in interests.split(",") if x.strip()],
            "existing_skills": [x.strip() for x in skills.split(",") if x.strip()],
            "weekly_learning_goal": goal,
        }
        if api("PUT", "/profile", json=payload):
            initial_profile.clear()
            st.success("Profile saved to local SQLite memory. Refresh recommendations to personalize them.")
            st.rerun()
    st.caption("Optional: set USE_OLLAMA=1 in the FastAPI terminal to add local Qwen summaries and coaching comments. The deterministic fallback works without Ollama.")
