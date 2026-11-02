"""Offline integration tests for persistent, multi-turn career coaching."""
from fastapi.testclient import TestClient
from backend.main import app


def test_adaptive_three_turn_interview(tmp_path, monkeypatch):
    monkeypatch.setenv("COWORKER_DB", str(tmp_path / "coach.sqlite"))
    monkeypatch.setenv("USE_OLLAMA", "0")
    client = TestClient(app)
    started = client.post("/career/interview/start", json={"topic": "RAG", "max_turns": 3})
    assert started.status_code == 200, started.text
    session = started.json()
    assert session["status"] == "active" and session["current_question"]["topic"] == "RAG"
    session_id = session["session_id"]
    first = client.post(f"/career/interview/{session_id}/answer", json={"answer": "Retrieval searches."})
    assert first.status_code == 200, first.text
    session = first.json()
    assert len(session["turns"]) == 1
    assert session["current_question"]["prompt"].startswith("Follow-up 2")
    assert "grounding" in session["current_question"]["prompt"]
    assert session["turns"][0]["assessment"]["gaps"]
    # Simulate a refresh by loading from a new request; history must survive.
    loaded = client.get(f"/career/interview/{session_id}")
    assert loaded.status_code == 200
    assert loaded.json()["turns"] == session["turns"]
    second = client.post(f"/career/interview/{session_id}/answer", json={"answer": "Pass documents as context to the model."})
    assert second.status_code == 200
    assert len(second.json()["turns"]) == 2
    third = client.post(f"/career/interview/{session_id}/answer", json={"answer": "Check citations against evidence and supporting passages."})
    assert third.status_code == 200
    assert third.json()["status"] == "completed"
    assert third.json()["current_question"] is None
    assert "Interview finished" in third.json()["final_feedback"]
    report = client.get("/career/report").json()
    assert report["attempts"] == 3
    assert report["interview_sessions_completed"] == 1
    assert client.post(f"/career/interview/{session_id}/answer", json={"answer": "extra"}).status_code == 400


def test_end_early_and_bad_session(tmp_path, monkeypatch):
    monkeypatch.setenv("COWORKER_DB", str(tmp_path / "end.sqlite"))
    monkeypatch.setenv("USE_OLLAMA", "0")
    client = TestClient(app)
    start = client.post("/career/interview/start", json={"topic": "Python coding", "max_turns": 4}).json()
    result = client.post(f"/career/interview/{start['session_id']}/end")
    assert result.status_code == 200
    assert result.json()["status"] == "ended"
    assert client.get(f"/career/interview/{start['session_id']}").json()["status"] == "ended"
    assert client.get("/career/interview/missing").status_code == 404
    assert client.post("/career/interview/start", json={"topic": "unknown"}).status_code == 400
    assert client.post("/career/interview/start", json={"topic": "RAG", "max_turns": 8}).status_code == 422
