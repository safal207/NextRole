from nextrole.agentcore_app import handle_payload


def test_agentcore_requires_prompt_without_invoking_model() -> None:
    called = False

    def runner(prompt: str):
        nonlocal called
        called = True
        return prompt

    result = handle_payload({}, runner=runner)

    assert result["ok"] is False
    assert result["error"] == "prompt_required"
    assert called is False


def test_agentcore_invokes_injected_strands_runner() -> None:
    seen: list[str] = []

    def runner(prompt: str):
        seen.append(prompt)
        return "one strong role needs a human decision"

    result = handle_payload(
        {"prompt": "Triage these opportunities and surface only real decisions."},
        runner=runner,
    )

    assert seen == ["Triage these opportunities and surface only real decisions."]
    assert result == {
        "ok": True,
        "agent": "NextRole",
        "framework": "Strands Agents",
        "human_authority": "required_for_application",
        "result": "one strong role needs a human decision",
    }
