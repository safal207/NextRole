from __future__ import annotations

import os

from strands import Agent

from .tools import assess_job_opportunity, create_human_decision_packet, triage_job_batch


SYSTEM_PROMPT = """You are NextRole, an autonomous job-search agent.

Your job is to reduce repetitive job-search work while preserving human authority over real career decisions.

Rules:
1. When multiple opportunities are available, use triage_job_batch before discussing them.
2. For a single opportunity, use assess_job_opportunity before making a recommendation.
3. Do not invent fit scores or missing skills when a tool result is available.
4. Low-fit opportunities should not consume human attention unless the human asks for them.
5. Strong opportunities should be converted into a concise human decision packet.
6. Never claim that an application was submitted unless an external application tool actually confirms it.
7. Never submit an application without an explicit human decision authorizing that action.
8. Explain material gaps plainly. Do not hide weaknesses to make a job look better.
9. Prefer a short decision queue over a long list of jobs.

The product principle is: It does the search. The human makes the career decisions.
"""


def build_agent(model_id: str | None = None) -> Agent:
    """Build the NextRole Strands agent.

    By default Strands uses its Amazon Bedrock provider. NEXTROLE_MODEL_ID can pin
    a specific Bedrock model for a deployment without hard-coding credentials or
    region-specific configuration into the repository.
    """

    selected_model = model_id or os.getenv("NEXTROLE_MODEL_ID", "").strip()
    kwargs = {
        "system_prompt": SYSTEM_PROMPT,
        "tools": [triage_job_batch, assess_job_opportunity, create_human_decision_packet],
    }
    if selected_model:
        kwargs["model"] = selected_model
    return Agent(**kwargs)


def main() -> None:
    agent = build_agent()
    print("NextRole is ready. Give it job opportunities and a candidate profile.")
    while True:
        try:
            message = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        if not message:
            continue
        if message.lower() in {"exit", "quit"}:
            return
        result = agent(message)
        print(f"\nNextRole> {result}")


if __name__ == "__main__":
    main()
