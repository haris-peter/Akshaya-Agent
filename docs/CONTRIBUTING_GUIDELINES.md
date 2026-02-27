# `/docs/CONTRIBUTING_GUIDELINES.md`

Since this project relies heavily on coding agents, these guidelines strictly restrict and define agent behavior to prevent drift.

## 1. Agent Restrictions
- **No business logic inside API routes**: `app/api` must only contain FastAPI input/output structures.
- **No eligibility logic inside LLM prompts**: Agents must not ask an LLM to determine application status.
- **No direct DB calls inside graph nodes**: The orchestration layer (`app/graph`) routes execution; it does not read/write to PostgreSQL directly.
- **All changes must update documentation first**: Every structural change must be reflected in the relevant `docs/*` file before the code change is made.

## 2. Testability
- Every agent must have an isolated unit test in `tests/test_agents.py`.
- Rules engines must have exhaustive condition tests in `tests/test_rules.py`.
- LangGraph orchestration flows should be mockable and tested in `tests/test_graph.py`.

## 3. Pull Requests (AI or Human)
- Agent PRs must include the updated `ApplicationState` trace for review.
- Any change to deterministic rules must include a rationale mapped back to real-world policy analogs.
