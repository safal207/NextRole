# NextRole

> **Your autonomous job-search agent.**
>
> **It does the search. You make the career decisions.**

NextRole is a new AI agent being built for the **Agents for Humans Hackathon** with the **Strands Agents SDK**.

Instead of giving a job seeker another dashboard to babysit, NextRole is designed to handle repetitive job-search work in the background: evaluate opportunities, explain fit and gaps, prepare the next action, and surface only when a real human career decision is needed.

## Hackathon MVP

One narrow end-to-end workflow:

```text
job opportunities
      ↓
Strands Agent
      ↓
structured fit / gaps / risk analysis
      ↓
low-fit opportunity → skip recommendation
      ↓
high-fit opportunity → prepare application draft
      ↓
Human Decision Gate
      ↓
APPLY / SKIP / WHY?
      ↓
decision trace
```

The agent may recommend and prepare. **The human remains the authority for the final application decision.**

## Why this matters

Job searching is full of repetitive work that still contains high-stakes human judgment. People repeatedly scan descriptions, compare requirements, identify gaps, tailor applications, and decide where to spend their limited attention.

NextRole aims to automate the repetitive layer without automating away the decision that affects the person's career.

## Planned hackathon stack

- Python 3.10+
- Strands Agents SDK
- Amazon Bedrock model provider
- deterministic job-analysis and human-decision tools
- Amazon Bedrock AgentCore deployment (target, if deployment validation is successful)
- lightweight web demo

## Project status

🚧 Early hackathon build. This repository was created during the 2026 Agents for Humans submission period.

The first milestone is a working local Strands agent with a deterministic demo dataset and a human decision gate. The second milestone is a live AWS deployment.

## Pre-existing work disclosure

NextRole is a **new hackathon project**. The author has earlier independent repositories exploring career analysis and human-verification primitives, including `CareerOS` and `ProofTask`.

No claim is made that those earlier projects were created for this hackathon. Any pre-existing code actually incorporated into NextRole will be identified explicitly in [`PREEXISTING_WORK.md`](PREEXISTING_WORK.md), including its source and role. New Strands orchestration, the NextRole product flow, hackathon UX, integration, tests, architecture, and deployment are developed in this repository during the submission period.

## License

MIT — see [`LICENSE`](LICENSE).
