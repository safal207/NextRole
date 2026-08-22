# One-time AWS OIDC bootstrap for NextRole

This is the one manual trust-establishment step before ChatGPT can operate the existing GitHub -> AWS deployment bridge through repository changes and GitHub Actions evidence.

## What this creates

- an AWS IAM OIDC provider for `https://token.actions.githubusercontent.com` if the account does not already have one;
- an IAM role named `NextRoleGitHubDeployRole` by default;
- a trust relationship restricted to the immutable OIDC subject for **only** `safal207/NextRole` on `main`;
- development/hackathon permissions required by the current Amazon Bedrock AgentCore CLI deployment path;
- GitHub repository variables `AWS_ROLE_ARN`, `AWS_REGION`, and `AWS_DEPLOY_ENABLED=false`.

No AWS access key is created or stored in GitHub.

## Immutable GitHub subject

NextRole was created after GitHub's July 15, 2026 immutable-subject rollout. The role therefore trusts:

```text
repo:safal207@55020240/NextRole@1342506311:ref:refs/heads/main
```

The audience is restricted to:

```text
sts.amazonaws.com
```

## Before running

You need an AWS identity that is allowed to create the one-time IAM/CloudFormation resources and a GitHub CLI login that can set Actions variables on `safal207/NextRole`.

Required local tools:

```text
aws
gh
```

The current AgentCore CLI deploy flow also uses AWS CDK. Bootstrap the target AWS account/region once before enabling GitHub deployment.

## Fast path

From the NextRole repository root:

```bash
./scripts/bootstrap-aws-oidc.sh us-east-1
```

The region can be replaced with the region where you will use Amazon Bedrock and AgentCore.

The script:

1. verifies the current AWS and GitHub identities;
2. detects whether the AWS account already has the GitHub OIDC provider;
3. deploys `infra/github-oidc-role.yaml` with CloudFormation;
4. reads the role ARN from the stack output;
5. writes the non-secret role ARN and region into GitHub Actions variables;
6. intentionally leaves `AWS_DEPLOY_ENABLED=false`.

## CDK bootstrap

The current AgentCore CLI uses AWS CDK/CloudFormation. Before enabling the bridge, bootstrap the target account/region with an administrative setup identity:

```bash
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REGION="us-east-1"
npx aws-cdk@latest bootstrap "aws://${ACCOUNT_ID}/${REGION}"
```

Use the same region that was passed to `bootstrap-aws-oidc.sh`.

## Enable the bridge

Only after the IAM role, CDK bootstrap, and Bedrock model access are ready:

```bash
gh variable set AWS_DEPLOY_ENABLED \
  --repo safal207/NextRole \
  --body true
```

Optional model pin:

```bash
gh variable set NEXTROLE_MODEL_ID \
  --repo safal207/NextRole \
  --body '<BEDROCK_MODEL_OR_INFERENCE_PROFILE_ID>'
```

Once enabled, changing `.deploy/oidc-trigger.json` on `main` starts `.github/workflows/deploy-agentcore-oidc.yml`.

## Emergency stop

```bash
gh variable set AWS_DEPLOY_ENABLED \
  --repo safal207/NextRole \
  --body false
```

This disables the deploy job without deleting AWS resources or credentials.

## Security scope

This bootstrap intentionally targets a **hackathon/development deployment**, not a final production account policy. Amazon's AgentCore documentation notes that CLI-generated/development deployment permissions are broad and should be replaced with resource-scoped least-privilege permissions for production.

After the first runtime exists and its concrete ARNs are known, tighten the deployment role to those runtime, bucket, build, log, and execution-role resources.
