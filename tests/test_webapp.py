from __future__ import annotations

from fastapi.testclient import TestClient

import nextrole.webapp as webapp


client = TestClient(webapp.app)


def test_health_and_ui_load() -> None:
    assert client.get("/health").json() == {"status": "ok", "service": "nextrole"}
    response = client.get("/")
    assert response.status_code == 200
    assert "It does the search" in response.text


def test_triage_api_exposes_one_human_decision() -> None:
    response = client.get("/api/triage")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total_jobs"] == 5
    assert payload["counts"] == {"surfaced": 1, "review": 2, "skipped": 2}
    assert payload["surfaced"][0]["job_id"] == "job-001"


def test_apply_records_authorizing_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(webapp, "ARTIFACT_DIR", tmp_path)

    response = client.post(
        "/api/decision",
        json={
            "job_id": "job-001",
            "decision": "APPLY",
            "rationale": "Evidence-backed fit.",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["decision"] == "APPLY"
    assert payload["application_authorized"] is True
    assert payload["trace_id"].startswith("sha256:")
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_why_never_authorizes_application(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(webapp, "ARTIFACT_DIR", tmp_path)

    response = client.post(
        "/api/decision",
        json={"job_id": "job-001", "decision": "WHY", "rationale": "Explain it."},
    )
    assert response.status_code == 200
    assert response.json()["application_authorized"] is False


def test_low_fit_job_cannot_enter_human_decision_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(webapp, "ARTIFACT_DIR", tmp_path)

    response = client.post(
        "/api/decision",
        json={"job_id": "job-003", "decision": "APPLY"},
    )
    assert response.status_code == 409
