# NextRole

> **Your autonomous job-search agent.**
>
> **It does the search. You make the career decisions.**

NextRole is a new AI agent being built for the **Agents for Humans Hackathon** with the **Strands Agents SDK**.

Instead of giving a job seeker another dashboard to babysit, NextRole is designed to handle repetitive job-search work in the background: evaluate opportunities, explain fit and gaps, reduce low-value noise, and surface only when a real human career decision is needed.

## Hackathon MVP

One narrow end-to-end workflow:

```text
job opportunities
      ↓
Strands Agent + triage_job_batch tool
      ↓
deterministic fit / gap evidence
      ↓
low-fit opportunity → quiet SKIP bucket
medium-fit opportunity → REVIEW bucket
strong opportunity → Human Decision Queue
      ↓
APPLY / SKIP / WHY?
      ↓
deterministic decision trace
```

The agent may analyze, prioritize and prepare. **The human remains the authority for the final application decision.**

## Judge-friendly web demo

Install and launch the local UI:

```bash
python -m pip install -e ".[dev]"
nextrole-web
```

Then open:

```text
http://localhost:8080
```

The dashboard shows the complete demo boundary in one screen: five opportunities are triaged into `2 SKIP`, `2 REVIEW`, and `1 HUMAN_DECISION`. The human-facing card exposes the evidence-backed `APPLY / SKIP / WHY` decision. A click calls the real FastAPI decision endpoint and persists a SHA-256 decision trace.

Useful endpoints:

```text
GET  /health
GET  /api/triage
POST /api/decision
```

## Runnable CLI fixture

You can also run the deterministic fixture without a browser:

```bash
pytest -q
PYTHONPATH=src python demo/run_demo.py
```

The fixture contains several deliberately different jobs. NextRole sorts them into `surfaced`, `review`, and `skipped` buckets. A strong opportunity receives an `APPLY / SKIP / WHY` packet; the CLI demo records an explicit human `APPLY` choice as a deterministic SHA-256 decision trace.

The trace records the exact opportunity, assessment, human choice, rationale, and whether application action was authorized. The trace is evidence of the decision boundary; it is **not** a claim that an external application was submitted.

## Strands integration

`src/nextrole/agent.py` defines the NextRole Strands agent. Its tools currently include:

- `triage_job_batch` — batch job triage with a short human interrupt queue
- `assess_job_opportunity` — transparent deterministic scoring for one role
- `create_human_decision_packet` — generates the human-facing APPLY / SKIP / WHY boundary

The LLM is not allowed to invent fit scores when deterministic tool evidence exists, and it is not allowed to claim an application was submitted without external confirmation.

## Why this matters

Job searching is full of repetitive work that still contains high-stakes human judgment. People repeatedly scan descriptions, compare requirements, identify gaps, tailor applications, and decide where to spend their limited attention.

NextRole aims to automate the repetitive layer without automating away the decision that affects the person's career.

## Planned hackathon stack

- Python 3.10+
- Strands Agents SDK
- FastAPI judge demo
- Amazon Bedrock model provider
- deterministic job-analysis and human-decision tools
- Amazon Bedrock AgentCore deployment (target, if deployment validation is successful)

## Project status

🚧 Active hackathon build. This repository was created during the 2026 Agents for Humans submission period.

Current milestone:

- batch triage fixture
- deterministic fit/gap scoring
- Strands batch and single-opportunity tools
- human decision gate
- deterministic persisted decision trace
- judge-friendly FastAPI UI wired to the real workflow
- regression tests and GitHub Actions CI

Next milestone: deploy the working flow on AWS / AgentCore and validate the live judge path.

See [`docs/architecture.md`](docs/architecture.md) for the current boundary and deployment plan.

## Pre-existing work disclosure

NextRole is a **new hackathon project**. The author has earlier independent repositories exploring career analysis and human-verification primitives, including `CareerOS` and `ProofTask`.

No claim is made that those earlier projects were created for this hackathon. Any pre-existing code actually incorporated into NextRole will be identified explicitly in [`PREEXISTING_WORK.md`](PREEXISTING_WORK.md), including its source and role. New Strands orchestration, the NextRole product flow, hackathon UX, integration, tests, architecture, and deployment are developed in this repository during the submission period.

## License

MIT — see [`LICENSE`](LICENSE).
