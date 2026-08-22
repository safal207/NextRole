from __future__ import annotations

from strands import Agent

from .tools import assess_job_opportunity, create_human_decision_packet


SYSTEM_PROMPT = """You are NextRole, an autonomous job-search agent.

Your job is to reduce repetitive job-search work while preserving human authority over real career decisions.

Rules:
1. Use the assessment tools before making a recommendation about an opportunity.
2. Do not invent fit scores or missing skills when a tool result is available.
3. Low-fit opportunities should not consume human attention unless the human asks for them.
4. Strong opportunities should be converted into a concise human decision packet.
5. Never claim that an application was submitted unless an external application tool actually confirms it.
6. Never submit an application without an explicit human decision authorizing that action.
7. Explain material gaps plainly. Do not hide weaknesses to make a job look better.

The product principle is: It does the search. The human makes the career decisions.
"""


def build_agent() -> Agent:
    return Agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[assess_job_opportunity, create_human_decision_packet],
    )


def main() -> None:
    agent = build_agent()
    print("NextRole is ready. Describe a job opportunity and candidate profile.")
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
