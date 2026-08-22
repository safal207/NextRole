from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .core import JobAssessment, assess_job, build_human_decision_packet


@dataclass(frozen=True)
class CandidateProfile:
    skills: tuple[str, ...]
    target_roles: tuple[str, ...]
    must_have_skills: tuple[str, ...]


@dataclass(frozen=True)
class JobOpportunity:
    job_id: str
    title: str
    company: str
    description: str
    url: str = ""


@dataclass(frozen=True)
class TriageResult:
    surfaced: tuple[dict, ...]
    review: tuple[dict, ...]
    skipped: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "surfaced": list(self.surfaced),
            "review": list(self.review),
            "skipped": list(self.skipped),
            "counts": {
                "surfaced": len(self.surfaced),
                "review": len(self.review),
                "skipped": len(self.skipped),
            },
        }


def assess_opportunity(job: JobOpportunity, profile: CandidateProfile) -> JobAssessment:
    return assess_job(
        title=job.title,
        company=job.company,
        description=job.description,
        candidate_skills=profile.skills,
        target_roles=profile.target_roles,
        must_have_skills=profile.must_have_skills,
    )


def triage_jobs(jobs: Iterable[JobOpportunity], profile: CandidateProfile) -> TriageResult:
    surfaced: list[dict] = []
    review: list[dict] = []
    skipped: list[dict] = []

    for job in jobs:
        assessment = assess_opportunity(job, profile)
        record = {
            "job_id": job.job_id,
            "url": job.url,
            "assessment": assessment.to_dict(),
        }

        if assessment.recommendation == "HUMAN_DECISION":
            record["decision_packet"] = build_human_decision_packet(assessment)
            surfaced.append(record)
        elif assessment.recommendation == "REVIEW":
            review.append(record)
        else:
            skipped.append(record)

    surfaced.sort(key=lambda item: (-item["assessment"]["fit_score"], item["job_id"]))
    review.sort(key=lambda item: (-item["assessment"]["fit_score"], item["job_id"]))
    skipped.sort(key=lambda item: (-item["assessment"]["fit_score"], item["job_id"]))
    return TriageResult(tuple(surfaced), tuple(review), tuple(skipped))


def _canonical_json(value: Mapping) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def create_decision_trace(
    *,
    job: JobOpportunity,
    assessment: JobAssessment,
    human_decision: str,
    rationale: str = "",
) -> dict:
    """Create a deterministic evidence record for a human career decision.

    APPLY and SKIP are terminal decisions. WHY records a request for explanation and
    does not authorize application submission.
    """

    decision = human_decision.strip().upper()
    if decision not in {"APPLY", "SKIP", "WHY"}:
        raise ValueError("human_decision must be APPLY, SKIP, or WHY")

    payload = {
        "version": "nextrole-decision-trace-v1",
        "job": asdict(job),
        "assessment": assessment.to_dict(),
        "human_decision": decision,
        "rationale": rationale.strip(),
        "application_authorized": decision == "APPLY",
    }
    trace_id = sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return {**payload, "trace_id": f"sha256:{trace_id}"}


def persist_decision_trace(trace: Mapping, path: str | Path) -> Path:
    """Persist one immutable-style trace artifact without changing its hash semantics."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(trace), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def jobs_from_dicts(items: Sequence[Mapping[str, str]]) -> list[JobOpportunity]:
    return [
        JobOpportunity(
            job_id=item["job_id"],
            title=item["title"],
            company=item["company"],
            description=item["description"],
            url=item.get("url", ""),
        )
        for item in items
    ]
