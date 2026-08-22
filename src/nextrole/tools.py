from __future__ import annotations

from strands import tool

from .core import assess_job, build_human_decision_packet
from .workflow import CandidateProfile, jobs_from_dicts, triage_jobs


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
def triage_job_batch(
    jobs: list[dict],
    candidate_skills: list[str],
    target_roles: list[str],
    must_have_skills: list[str],
) -> dict:
    """Triage a batch of job opportunities and return only meaningful human interrupts.

    Each job must contain job_id, title, company, and description. URL is optional.
    Strong matches are surfaced with APPLY / SKIP / WHY options; low-fit jobs stay
    out of the human queue.
    """

    profile = CandidateProfile(
        skills=tuple(candidate_skills),
        target_roles=tuple(target_roles),
        must_have_skills=tuple(must_have_skills),
    )
    opportunities = jobs_from_dicts(jobs)
    return triage_jobs(opportunities, profile).to_dict()


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
