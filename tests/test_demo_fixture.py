from __future__ import annotations

import json
from pathlib import Path

from nextrole.workflow import CandidateProfile, jobs_from_dicts, triage_jobs


def test_demo_fixture_has_one_real_human_interrupt() -> None:
    data = json.loads(Path("demo/jobs.json").read_text(encoding="utf-8"))
    profile = CandidateProfile(
        skills=tuple(data["candidate"]["skills"]),
        target_roles=tuple(data["candidate"]["target_roles"]),
        must_have_skills=tuple(data["candidate"]["must_have_skills"]),
    )

    result = triage_jobs(jobs_from_dicts(data["jobs"]), profile)

    assert result.to_dict()["counts"] == {"surfaced": 1, "review": 2, "skipped": 2}
    assert result.surfaced[0]["job_id"] == "job-001"
    assert result.surfaced[0]["assessment"]["company"] == "Northstar Bank"
