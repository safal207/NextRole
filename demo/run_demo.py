from __future__ import annotations

import json
from pathlib import Path

from nextrole.workflow import (
    CandidateProfile,
    create_decision_trace,
    jobs_from_dicts,
    triage_jobs,
)


FIXTURE = Path(__file__).with_name("jobs.json")


def main() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    profile = CandidateProfile(
        skills=tuple(data["candidate"]["skills"]),
        target_roles=tuple(data["candidate"]["target_roles"]),
        must_have_skills=tuple(data["candidate"]["must_have_skills"]),
    )
    jobs = jobs_from_dicts(data["jobs"])
    result = triage_jobs(jobs, profile)

    print("NEXTROLE DEMO")
    print("=============")
    print(json.dumps(result.to_dict()["counts"], indent=2))

    print("\nHUMAN DECISION QUEUE")
    for item in result.surfaced:
        assessment = item["assessment"]
        print(
            f"- {assessment['title']} @ {assessment['company']} "
            f"| fit={assessment['fit_score']} | "
            f"options={item['decision_packet']['human_options']}"
        )

    if not result.surfaced:
        print("No opportunities require a human decision.")
        return

    selected = result.surfaced[0]
    selected_job = next(job for job in jobs if job.job_id == selected["job_id"])
    assessment = __import__("nextrole.workflow", fromlist=["assess_opportunity"]).assess_opportunity(
        selected_job, profile
    )
    trace = create_decision_trace(
        job=selected_job,
        assessment=assessment,
        human_decision="APPLY",
        rationale="Demo decision: strong fit and no missing must-have skills.",
    )

    print("\nHUMAN DECISION TRACE")
    print(json.dumps(trace, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
