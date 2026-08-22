from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_oidc_role_is_scoped_to_immutable_nextrole_main_subject() -> None:
    template = _read("infra/github-oidc-role.yaml")
    expected = "repo:safal207@55020240/NextRole@1342506311:ref:refs/heads/main"

    assert expected in template
    assert "token.actions.githubusercontent.com:aud: sts.amazonaws.com" in template
    assert "sts:AssumeRoleWithWebIdentity" in template


def test_oidc_workflow_uses_ephemeral_identity_not_static_keys() -> None:
    workflow = _read(".github/workflows/deploy-agentcore-oidc.yml")

    assert "id-token: write" in workflow
    assert "vars.AWS_ROLE_ARN" in workflow
    assert "aws-actions/configure-aws-credentials" in workflow
    assert "AWS_ACCESS_KEY_ID" not in workflow
    assert "AWS_SECRET_ACCESS_KEY" not in workflow


def test_bootstrap_leaves_deployment_disabled() -> None:
    script = _read("scripts/bootstrap-aws-oidc.sh")

    assert 'gh variable set AWS_DEPLOY_ENABLED --repo "$REPO" --body "false"' in script
    assert "AWS_DEPLOY_ENABLED=false" in script


def test_deploy_workflow_requires_explicit_enable_switch() -> None:
    workflow = _read(".github/workflows/deploy-agentcore-oidc.yml")

    assert "vars.AWS_DEPLOY_ENABLED == 'true'" in workflow
    assert 'paths:\n      - ".deploy/oidc-trigger.json"' in workflow
