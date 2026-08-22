from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable


_WORD = re.compile(r"[a-zA-Z0-9+#.\-]+")


@dataclass(frozen=True)
class JobAssessment:
    title: str
    company: str
    fit_score: int
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    recommendation: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_terms(values: Iterable[str]) -> set[str]:
    return {value.strip().lower() for value in values if value and value.strip()}


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _WORD.findall(text)}


def assess_job(
    *,
    title: str,
    company: str,
    description: str,
    candidate_skills: Iterable[str],
    target_roles: Iterable[str] = (),
    must_have_skills: Iterable[str] = (),
) -> JobAssessment:
    """Create a transparent, deterministic first-pass job assessment.

    This deliberately does not let an LLM invent the score. The agent can use the
    result as evidence when deciding what to surface to the human.
    """

    skills = _normalize_terms(candidate_skills)
    must_have = _normalize_terms(must_have_skills)
    targets = _normalize_terms(target_roles)
    haystack = _tokens(f"{title} {description}")

    matched = sorted(skill for skill in skills if skill in haystack)
    missing = sorted(skill for skill in must_have if skill not in haystack)

    skill_score = 0 if not skills else round(70 * len(matched) / len(skills))
    role_score = 0
    lowered_title = title.lower()
    if targets:
        role_score = 20 if any(target in lowered_title for target in targets) else 0
    else:
        role_score = 10

    must_have_penalty = min(30, 10 * len(missing))
    fit_score = max(0, min(100, skill_score + role_score + 10 - must_have_penalty))

    if fit_score >= 70 and not missing:
        recommendation = "HUMAN_DECISION"
        reason = "Strong enough to prepare an application and ask the human to decide."
    elif fit_score >= 45:
        recommendation = "REVIEW"
        reason = "Potential fit, but meaningful gaps should be reviewed before spending time applying."
    else:
        recommendation = "SKIP"
        reason = "Low first-pass fit; keep it out of the human's decision queue unless explicitly requested."

    return JobAssessment(
        title=title,
        company=company,
        fit_score=fit_score,
        matched_skills=tuple(matched),
        missing_skills=tuple(missing),
        recommendation=recommendation,
        reason=reason,
    )


def build_human_decision_packet(assessment: JobAssessment) -> dict:
    """Create the minimal artifact surfaced when a real career decision is needed."""

    return {
        "decision_required": assessment.recommendation == "HUMAN_DECISION",
        "job": {"title": assessment.title, "company": assessment.company},
        "fit_score": assessment.fit_score,
        "matched_skills": list(assessment.matched_skills),
        "missing_skills": list(assessment.missing_skills),
        "recommendation": assessment.recommendation,
        "reason": assessment.reason,
        "human_options": ["APPLY", "SKIP", "WHY"],
    }
