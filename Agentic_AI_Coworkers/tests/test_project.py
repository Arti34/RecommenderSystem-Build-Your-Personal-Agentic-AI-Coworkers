import os
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import Profile
from backend.articles import load_sample_articles, top_three, compose_brief
from backend.coach import analyze_role


def test_article_ranking_uses_three_sources():
    profile = Profile(interests=["RAG", "agentic AI"])
    selected = top_three(load_sample_articles(), profile)
    assert len(selected) == 3
    assert len({a.source for a in selected}) == 3
    assert all(a.mode == "sample_data" for a in selected)


def test_daily_demo_is_explicitly_labeled():
    brief = compose_brief(load_sample_articles(), Profile(), "sample_data")
    assert brief.reading_minutes == 18
    assert "OFFLINE SNAPSHOT" in brief.note
    assert len(brief.articles) == 3


def test_skill_gap_matching():
    result = analyze_role("Need Python, SQL, Docker and AWS skills", Profile(existing_skills=["Python", "SQL"]))
    assert "docker" in result["skills_to_explore"]
    assert "aws" in result["skills_to_explore"]
    assert "python" in result["skills_matching_profile"]


def test_full_api_demo_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("COWORKER_DB", str(tmp_path / "test.sqlite"))
    monkeypatch.setenv("USE_OLLAMA", "0")
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    p = client.get("/profile").json()
    assert "interests" in p
    assert client.put("/profile", json={**p, "target_role": "ML Engineer"}).status_code == 200
    brief = client.post("/daily-brief", json={"mode": "sample"})
    assert brief.status_code == 200, brief.text
    assert len(brief.json()["articles"]) == 3
    assert all(a["published_date"].startswith("2026-") for a in brief.json()["articles"])
    prep = client.post("/career/prepare", json={"mode": "sample"})
    assert prep.status_code == 200, prep.text
    assert len(prep.json()["opportunities"]) == 3
    q = prep.json()["next_question"]
    answer = client.post("/career/answer", json={
        "question_id": q["question_id"],
        "answer": "Retrieval searches documents, provides context for the model, and checks evidence citations."})
    assert answer.status_code == 200, answer.text
    assert answer.json()["score"] > 0
    mark = client.post("/reading/mark-read", json={"title": "Read demo", "url": "https://example.org/article"})
    assert mark.status_code == 200
    assert client.get("/reading/history").json()["count"] == 1
    report = client.get("/career/report")
    assert report.status_code == 200
    assert report.json()["attempts"] == 1
    assert report.json()["average_score"] is not None


def test_unknown_question_error(tmp_path, monkeypatch):
    monkeypatch.setenv("COWORKER_DB", str(tmp_path / "test.sqlite"))
    client = TestClient(app)
    resp = client.post("/career/answer", json={"question_id": "does-not-exist", "answer": "Hello"})
    assert resp.status_code == 400
