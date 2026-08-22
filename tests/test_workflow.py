from __future__ import annotations

import json

from nextrole.workflow import (
    CandidateProfile,
    JobOpportunity,
    assess_opportunity,
    create_decision_trace,
    persist_decision_trace,
    triage_jobs,
)


PROFILE = CandidateProfile(
    skills=("api", "sql", "rest", "postman", "bpmn", "uml", "integrations", "manual testing"),
    target_roles=("qa engineer", "system analyst"),
    must_have_skills=("api", "sql"),
)


def test_multiword_skill_is_matched() -> None:
    job = JobOpportunity(
        job_id="job-multi",
        title="QA Engineer",
        company="Example",
        description="Manual testing, API, SQL, REST and Postman are core to this role.",
    )

    assessment = assess_opportunity(job, PROFILE)

    assert "manual testing" in assessment.matched_skills


def test_triage_only_surfaces_strong_opportunity() -> None:
    jobs = [
        JobOpportunity(
            job_id="strong",
            title="System Analyst — Payments",
            company="Bank",
            description=(
                "API REST integrations SQL BPMN UML Postman integrations and manual testing "
                "for payment services."
            ),
        ),
        JobOpportunity(
            job_id="weak",
            title="Product Designer",
            company="Design Co",
            description="Figma prototyping user research and visual design.",
        ),
    ]

    result = triage_jobs(jobs, PROFILE)

    assert [item["job_id"] for item in result.surfaced] == ["strong"]
    assert [item["job_id"] for item in result.skipped] == ["weak"]
    assert result.surfaced[0]["decision_packet"]["human_options"] == ["APPLY", "SKIP", "WHY"]


def test_apply_decision_trace_is_deterministic_and_authorizes_application() -> None:
    job = JobOpportunity(
        job_id="strong",
        title="System Analyst — Payments",
        company="Bank",
        description="API REST integrations SQL BPMN UML Postman and manual testing.",
        url="https://example.test/jobs/strong",
    )
    assessment = assess_opportunity(job, PROFILE)

    first = create_decision_trace(
        job=job,
        assessment=assessment,
        human_decision="APPLY",
        rationale="Strong fit.",
    )
    second = create_decision_trace(
        job=job,
        assessment=assessment,
        human_decision="APPLY",
        rationale="Strong fit.",
    )

    assert first == second
    assert first["application_authorized"] is True
    assert first["trace_id"].startswith("sha256:")


def test_why_does_not_authorize_application() -> None:
    job = JobOpportunity(
        job_id="strong",
        title="System Analyst — Payments",
        company="Bank",
        description="API REST integrations SQL BPMN UML Postman and manual testing.",
    )
    assessment = assess_opportunity(job, PROFILE)

    trace = create_decision_trace(
        job=job,
        assessment=assessment,
        human_decision="WHY",
    )

    assert trace["application_authorized"] is False


def test_trace_can_be_persisted_without_mutation(tmp_path) -> None:
    job = JobOpportunity(
        job_id="persisted",
        title="QA Engineer",
        company="Example",
        description="API SQL REST Postman manual testing.",
    )
    assessment = assess_opportunity(job, PROFILE)
    trace = create_decision_trace(
        job=job,
        assessment=assessment,
        human_decision="SKIP",
        rationale="Human chose not to pursue this role.",
    )

    path = persist_decision_trace(trace, tmp_path / "decision-trace.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded == trace
    assert loaded["application_authorized"] is False
