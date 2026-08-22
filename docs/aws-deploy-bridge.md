# NextRole AWS deployment bridge

This bridge lets GitHub Actions act as the controlled connection between the NextRole repository and AWS. Once one authentication option is configured, a deployment can be requested by changing a small trigger file in the repository. The workflow then validates NextRole, authenticates to AWS, deploys the existing Strands agent to Amazon Bedrock AgentCore, performs a smoke invocation, and uploads deployment evidence.

Both workflows are **disabled by default**. A repository variable named `AWS_DEPLOY_ENABLED` must equal `true` before either deploy job can run.

## Shared repository variables

Configure these under **Settings → Secrets and variables → Actions → Variables**:

- `AWS_DEPLOY_ENABLED` = `false` during setup; change to `true` only when ready
- `AWS_REGION` = the target region, for example `us-east-1`
- `NEXTROLE_MODEL_ID` = optional Bedrock model ID to pin; leave unset to use the Strands default

Only enable one authentication workflow at a time for normal use.

---

## Option A — GitHub OIDC (recommended)

Workflow: `.github/workflows/deploy-agentcore-oidc.yml`

This uses short-lived AWS credentials. No AWS access keys are stored in GitHub.

### 1. Add the GitHub OIDC provider to AWS IAM

Provider URL:

```text
https://token.actions.githubusercontent.com
```

Audience:

```text
sts.amazonaws.com
```

### 2. Create an IAM role for the deployment workflow

The trust policy should restrict the role to this exact new repository and the `main` branch.

NextRole was created after GitHub's July 15, 2026 immutable OIDC subject change, so its expected subject is:

```text
repo:safal207@55020240/NextRole@1342506311:ref:refs/heads/main
```

Trust-policy shape:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:safal207@55020240/NextRole@1342506311:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Attach the IAM permissions required by the **AgentCore CLI IAM Permissions** documentation for deployment. The AgentCore CLI uses direct AgentCore API calls plus AWS CDK/CloudFormation during deployment, so a role that can only invoke a model is not sufficient.

### 3. Add the role ARN as a GitHub repository variable

```text
AWS_ROLE_ARN=arn:aws:iam::<AWS_ACCOUNT_ID>:role/<YOUR_ROLE_NAME>
```

### 4. Enable and trigger

Set:

```text
AWS_DEPLOY_ENABLED=true
```

Then increment `nonce` in:

```text
.deploy/oidc-trigger.json
```

A push to `main` that changes that file starts the OIDC deployment workflow.

---

## Option B — GitHub Secrets with an IAM access key (fastest setup)

Workflow: `.github/workflows/deploy-agentcore-static.yml`

This is simpler, but it uses long-lived credentials and therefore has more credential-management risk.

### 1. Create an AWS IAM identity for deployment

Give it the permissions required by the AgentCore CLI deployment documentation. Do not use a root account key.

### 2. Add GitHub repository secrets

Under **Settings → Secrets and variables → Actions → Secrets**, add:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

Never put either value in source code, trigger files, issues, logs, or chat messages.

### 3. Enable and trigger

Set:

```text
AWS_DEPLOY_ENABLED=true
```

Then increment `nonce` in:

```text
.deploy/static-trigger.json
```

A push to `main` that changes that file starts the static-credentials deployment workflow.

---

## What the bridge does

Each deployment workflow:

1. checks out the exact `main` revision;
2. installs Python 3.11 and Node.js 22;
3. authenticates to AWS using the selected option;
4. runs `pytest -q` before touching deployment;
5. installs the current `@aws/agentcore` CLI;
6. creates a temporary AgentCore project;
7. adds the existing NextRole code as a BYO Python/Strands/Bedrock agent;
8. runs `agentcore validate`;
9. runs `agentcore deploy -y`;
10. captures `agentcore status`;
11. performs one smoke `agentcore invoke`;
12. uploads validate/deploy/status/invoke evidence as a GitHub Actions artifact.

The temporary AgentCore project is created on the ephemeral GitHub runner. AWS deployment state is the authority; generated workspace files are not committed back to the repository.

## How ChatGPT can operate it after setup

Once AWS auth is configured and `AWS_DEPLOY_ENABLED=true`, ChatGPT with access to this repository can request a deployment by updating the appropriate trigger JSON on `main`. It can then inspect the GitHub Actions run, jobs, logs and deployment evidence from the connected GitHub app.

This is a bridge rather than a native AWS connector: AWS credentials remain in AWS/GitHub, while ChatGPT only operates the already-authorized GitHub surface.

## Safety switch

To stop all automatic bridge deployments immediately, set:

```text
AWS_DEPLOY_ENABLED=false
```

Changing source code does not trigger either deployment workflow. Only the selected `.deploy/*-trigger.json` file does.
