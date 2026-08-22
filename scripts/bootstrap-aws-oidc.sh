#!/usr/bin/env bash
set -euo pipefail

REPO="safal207/NextRole"
STACK_NAME="${NEXTROLE_OIDC_STACK_NAME:-nextrole-github-oidc}"
REGION="${1:-${AWS_REGION:-us-east-1}}"
ROLE_NAME="${NEXTROLE_OIDC_ROLE_NAME:-NextRoleGitHubDeployRole}"
TEMPLATE="infra/github-oidc-role.yaml"
GITHUB_PROVIDER_SUFFIX="oidc-provider/token.actions.githubusercontent.com"
CDK_BOOTSTRAP_PARAMETER="/cdk-bootstrap/hnb659fds/version"

for cmd in aws gh; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: '$cmd' is required." >&2
    exit 1
  fi
done

if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: run this script from the NextRole repository root." >&2
  exit 1
fi

echo "==> AWS identity"
aws sts get-caller-identity --region "$REGION"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text --region "$REGION")"

echo "==> GitHub identity"
gh auth status

EXISTING_PROVIDER_ARN="$(
  aws iam list-open-id-connect-providers \
    --query "OpenIDConnectProviderList[?ends_with(Arn, '${GITHUB_PROVIDER_SUFFIX}')].Arn | [0]" \
    --output text
)"

if [[ -n "$EXISTING_PROVIDER_ARN" && "$EXISTING_PROVIDER_ARN" != "None" ]]; then
  CREATE_PROVIDER="false"
  echo "==> Reusing existing GitHub OIDC provider: $EXISTING_PROVIDER_ARN"
else
  CREATE_PROVIDER="true"
  EXISTING_PROVIDER_ARN=""
  echo "==> No GitHub OIDC provider found; CloudFormation will create it."
fi

echo "==> Deploying OIDC role stack '$STACK_NAME' in $REGION"
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    RoleName="$ROLE_NAME" \
    CreateGitHubOidcProvider="$CREATE_PROVIDER" \
    ExistingGitHubOidcProviderArn="$EXISTING_PROVIDER_ARN"

ROLE_ARN="$(
  aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='DeploymentRoleArn'].OutputValue | [0]" \
    --output text
)"

if [[ -z "$ROLE_ARN" || "$ROLE_ARN" == "None" ]]; then
  echo "ERROR: stack completed but DeploymentRoleArn output was not found." >&2
  exit 1
fi

CDK_VERSION="$(
  aws ssm get-parameter \
    --region "$REGION" \
    --name "$CDK_BOOTSTRAP_PARAMETER" \
    --query "Parameter.Value" \
    --output text 2>/dev/null || true
)"

if [[ -n "$CDK_VERSION" && "$CDK_VERSION" != "None" ]]; then
  echo "==> AWS CDK is already bootstrapped in $ACCOUNT_ID/$REGION (version $CDK_VERSION)."
else
  if ! command -v npx >/dev/null 2>&1; then
    echo "ERROR: CDK bootstrap is missing and 'npx' is not available. Install Node.js/npm, then rerun." >&2
    exit 1
  fi
  echo "==> Bootstrapping AWS CDK in $ACCOUNT_ID/$REGION"
  npx --yes aws-cdk@latest bootstrap "aws://${ACCOUNT_ID}/${REGION}"
fi

echo "==> Writing non-secret deployment variables to GitHub"
gh variable set AWS_ROLE_ARN --repo "$REPO" --body "$ROLE_ARN"
gh variable set AWS_REGION --repo "$REPO" --body "$REGION"
gh variable set AWS_DEPLOY_ENABLED --repo "$REPO" --body "false"

if [[ -n "${NEXTROLE_MODEL_ID:-}" ]]; then
  gh variable set NEXTROLE_MODEL_ID --repo "$REPO" --body "$NEXTROLE_MODEL_ID"
  echo "==> Pinned NEXTROLE_MODEL_ID from the current environment."
fi

cat <<EOF

OIDC bridge bootstrap complete.

AWS role:   $ROLE_ARN
AWS region: $REGION
Repository: $REPO
CDK:        bootstrapped
Safety:     AWS_DEPLOY_ENABLED=false

The bridge is deliberately disabled after bootstrap.
After Bedrock model access is confirmed, enable it with:

  gh variable set AWS_DEPLOY_ENABLED --repo $REPO --body true

Then NextRole deployments can be requested through .deploy/oidc-trigger.json.
EOF
