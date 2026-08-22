# NextRole on Amazon Bedrock AgentCore

NextRole includes an AgentCore Runtime entrypoint at:

```text
src/nextrole/agentcore_app.py
```

It uses the official `BedrockAgentCoreApp` wrapper around the existing Strands agent. The deployment path is intentionally BYO (bring your own code), so the hackathon repository stays the source of truth.

## What is already implemented

- Strands agent: `src/nextrole/agent.py`
- AgentCore entrypoint: `src/nextrole/agentcore_app.py`
- deterministic job tools and human decision boundary
- local web judge demo
- AgentCore payload tests that do not call a live model

## Prerequisites for a real AWS deployment

You need:

- AWS account and credentials
- IAM permissions required by AgentCore deployment
- Amazon Bedrock model access in the target AWS region
- Python 3.10+
- Node.js 20+
- the current AgentCore CLI (`@aws/agentcore`)

Do not commit AWS credentials or generated `.env.local` files.

## 1. Install and verify locally

From the NextRole repository root:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

The AgentCore wrapper can be run locally without creating AgentCore infrastructure:

```bash
nextrole-agentcore
```

Then invoke it from another terminal:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain why NextRole should interrupt me only for strong job matches."}'
```

This invocation uses the Strands Amazon Bedrock provider and therefore requires valid AWS credentials and model access.

Optional model pinning:

```bash
export NEXTROLE_MODEL_ID="<bedrock-model-id>"
```

If `NEXTROLE_MODEL_ID` is unset, NextRole lets Strands use its configured/default Amazon Bedrock model provider.

## 2. Install the current AgentCore CLI

```bash
npm install -g @aws/agentcore
agentcore --help
```

The current AWS CLI replaces the older `bedrock-agentcore-starter-toolkit`. Do not use both CLIs in the same environment.

## 3. Create deployment metadata and attach the existing NextRole code

Keep generated AgentCore infrastructure outside the source tree that is submitted as product code:

```bash
REPO_ROOT="$(pwd)"
mkdir -p .agentcore-work
agentcore create \
  --name NextRoleDeploy \
  --no-agent \
  --output-dir .agentcore-work \
  --skip-git
```

Enter the generated project directory, then add NextRole as BYO code. `--code-location` may be an absolute path; `--entrypoint` is relative to that location.

```bash
cd .agentcore-work/NextRoleDeploy

agentcore add agent \
  --name NextRoleAgent \
  --type byo \
  --code-location "$REPO_ROOT" \
  --entrypoint src/nextrole/agentcore_app.py \
  --language Python \
  --build CodeZip
```

Validate the generated AgentCore project before deployment:

```bash
agentcore validate
```

If the installed CLI version generates a slightly different project-directory name, use the directory printed by `agentcore create`; do not guess or hand-edit deployment state.

## 4. Local AgentCore dev check

Inside the generated AgentCore project:

```bash
agentcore dev --logs
```

Use a second terminal for a local prompt if supported by your installed CLI version, or invoke the runtime HTTP endpoint on port 8080.

## 5. Deploy

Only after local validation is green:

```bash
agentcore deploy -y
```

Then inspect the deployed state:

```bash
agentcore status --json
```

Invoke the deployed agent:

```bash
agentcore invoke "Triage job opportunities quietly and surface only real human career decisions."
```

## 6. Evidence to save for Devpost

After a successful real deployment, save these facts in the submission materials:

- AgentCore runtime/endpoint name
- deployed version
- AWS region
- successful `agentcore invoke` output
- screenshot of AgentCore status or observability
- exact Git commit deployed

Do **not** write “deployed on AgentCore” in the README or Devpost description until these facts have been observed from the real AWS account.

## Runtime boundary

AgentCore hosting does not weaken NextRole's authority model:

```text
Bedrock / Strands reasoning
        ↓
deterministic NextRole tools
        ↓
low value → quiet skip/review
        ↓
strong opportunity
        ↓
Human Decision Gate
        ↓
APPLY / SKIP / WHY
        ↓
deterministic decision trace
```

`APPLY` authorizes the next application action. It is not itself evidence that an external application was submitted.
