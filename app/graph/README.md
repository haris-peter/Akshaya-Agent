# `app/graph/`

This is your LangGraph brain.

## `state.py`
Contains:
```python
class ApplicationState(TypedDict):
    citizen_id: str
    scheme_id: str
    required_documents: list
    collected_documents: list
    eligibility_result: dict
    progress_log: list
```

## `workflow.py`
Defines nodes and edges.

## `conditions.py`
Contains branching logic. Keeps orchestration clean.
