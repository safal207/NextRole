from __future__ import annotations

from strands import tool

from .core import assess_job, build_human_decision_packet


@tool
def assess_job_opportunity(
    title: str,
    company: str,
    description: str,
    candidate_skills: list[str],
    target_roles: list[str],
    must_have_skills: list[str],
) -> dict:
    """Score one job opportunity using transparent deterministic evidence.

    Use this before recommending whether the opportunity should be skipped,
    reviewed, or surfaced to the human for an application decision.
    """

    assessment = assess_job(
        title=title,
        company=company,
        description=description,
        candidate_skills=candidate_skills,
        target_roles=target_roles,
        must_have_skills=must_have_skills,
    )
    return assessment.to_dict()


@tool
def create_human_decision_packet(
    title: str,
    company: str,
    description: str,
    candidate_skills: list[str],
    target_roles: list[str],
    must_have_skills: list[str],
) -> dict:
    """Create an APPLY / SKIP / WHY decision packet for a strong opportunity.

    The human remains the final authority. This tool never submits an application.
    """

    assessment = assess_job(
        title=title,
        company=company,
        description=description,
        candidate_skills=candidate_skills,
        target_roles=target_roles,
        must_have_skills=must_have_skills,
    )
    return build_human_decision_packet(assessment)
