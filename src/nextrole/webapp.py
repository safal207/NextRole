from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from .workflow import (
    CandidateProfile,
    JobOpportunity,
    assess_opportunity,
    create_decision_trace,
    jobs_from_dicts,
    persist_decision_trace,
    triage_jobs,
)


PACKAGE_DIR = Path(__file__).resolve().parent
WEB_DIR = PACKAGE_DIR / "web"
REPO_ROOT = PACKAGE_DIR.parents[1]
DEMO_FILE = REPO_ROOT / "demo" / "jobs.json"
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "decisions"

app = FastAPI(title="NextRole", version="0.2.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


class DecisionRequest(BaseModel):
    job_id: str
    decision: str
    rationale: str = ""


def _load_demo() -> tuple[CandidateProfile, list[JobOpportunity]]:
    if not DEMO_FILE.exists():
        raise RuntimeError(f"Demo fixture not found: {DEMO_FILE}")

    data = json.loads(DEMO_FILE.read_text(encoding="utf-8"))
    profile = CandidateProfile(
        skills=tuple(data["candidate"]["skills"]),
        target_roles=tuple(data["candidate"]["target_roles"]),
        must_have_skills=tuple(data["candidate"]["must_have_skills"]),
    )
    return profile, jobs_from_dicts(data["jobs"])


def _find_job(job_id: str, jobs: list[JobOpportunity]) -> JobOpportunity:
    for job in jobs:
        if job.job_id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "nextrole"}


@app.get("/api/triage")
def api_triage() -> dict:
    profile, jobs = _load_demo()
    result = triage_jobs(jobs, profile)
    payload = result.to_dict()
    payload["total_jobs"] = len(jobs)
    payload["profile"] = {
        "skills": list(profile.skills),
        "target_roles": list(profile.target_roles),
        "must_have_skills": list(profile.must_have_skills),
    }
    return payload


@app.post("/api/decision")
def api_decision(request: DecisionRequest) -> dict:
    decision = request.decision.strip().upper()
    if decision not in {"APPLY", "SKIP", "WHY"}:
        raise HTTPException(status_code=400, detail="Decision must be APPLY, SKIP, or WHY")

    profile, jobs = _load_demo()
    job = _find_job(request.job_id, jobs)
    assessment = assess_opportunity(job, profile)

    if assessment.recommendation != "HUMAN_DECISION":
        raise HTTPException(
            status_code=409,
            detail="This opportunity is not in the human decision queue.",
        )

    trace = create_decision_trace(
        job=job,
        assessment=assessment,
        human_decision=decision,
        rationale=request.rationale,
    )
    filename = trace["trace_id"].replace(":", "-") + ".json"
    artifact_path = persist_decision_trace(trace, ARTIFACT_DIR / filename)

    explanation = {
        "matched_skills": list(assessment.matched_skills),
        "missing_skills": list(assessment.missing_skills),
        "reason": assessment.reason,
    }

    return {
        "status": "recorded",
        "decision": decision,
        "application_authorized": trace["application_authorized"],
        "trace_id": trace["trace_id"],
        "artifact_path": str(artifact_path.relative_to(REPO_ROOT)),
        "explanation": explanation,
    }


def run() -> None:
    uvicorn.run("nextrole.webapp:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    run()
