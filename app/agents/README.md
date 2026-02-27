# `app/agents/`

This folder contains all intelligent agent logic.
Each file represents one agent node in the LangGraph workflow.

Agents must:
- Accept `ApplicationState`
- Return `ApplicationState`
- Not mutate unrelated fields
- Not perform orchestration logic

Eligibility logic must not exist here.
