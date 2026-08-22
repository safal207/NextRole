from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agent import build_agent


app = BedrockAgentCoreApp()
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def handle_payload(
    payload: Mapping[str, Any],
    *,
    runner: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    """Handle one AgentCore invocation without weakening the human-decision boundary.

    The AgentCore runtime is responsible for hosting/invocation. NextRole's Strands
    agent still uses deterministic tools for job evidence and may not claim an
    application was submitted without an external confirmed action.
    """

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {
            "ok": False,
            "error": "prompt_required",
            "message": "Provide a non-empty 'prompt' field.",
        }

    agent_runner = runner or _get_agent()
    result = agent_runner(prompt)
    return {
        "ok": True,
        "agent": "NextRole",
        "framework": "Strands Agents",
        "human_authority": "required_for_application",
        "result": str(result),
    }


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    return handle_payload(payload)


def run() -> None:
    app.run()


if __name__ == "__main__":
    run()
