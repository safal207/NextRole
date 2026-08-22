from nextrole.core import assess_job, build_human_decision_packet


def test_strong_match_surfaces_human_decision() -> None:
    assessment = assess_job(
        title="Senior QA Engineer",
        company="Example",
        description="Manual QA API SQL Postman regression testing",
        candidate_skills=["qa", "api", "sql", "postman"],
        target_roles=["qa"],
        must_have_skills=["api", "sql"],
    )

    assert assessment.fit_score >= 70
    assert assessment.recommendation == "HUMAN_DECISION"

    packet = build_human_decision_packet(assessment)
    assert packet["decision_required"] is True
    assert packet["human_options"] == ["APPLY", "SKIP", "WHY"]


def test_low_match_does_not_interrupt_human() -> None:
    assessment = assess_job(
        title="Senior iOS Engineer",
        company="Example",
        description="Swift SwiftUI iOS mobile architecture",
        candidate_skills=["qa", "api", "sql", "postman"],
        target_roles=["qa", "system analyst"],
        must_have_skills=["api", "sql"],
    )

    assert assessment.fit_score < 45
    assert assessment.recommendation == "SKIP"
    assert build_human_decision_packet(assessment)["decision_required"] is False


def test_missing_must_have_skill_prevents_strong_decision() -> None:
    assessment = assess_job(
        title="QA Engineer",
        company="Example",
        description="QA API Postman regression testing",
        candidate_skills=["qa", "api", "sql", "postman"],
        target_roles=["qa"],
        must_have_skills=["api", "sql"],
    )

    assert "sql" in assessment.missing_skills
    assert assessment.recommendation != "HUMAN_DECISION"
