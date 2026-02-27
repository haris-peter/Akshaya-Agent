# `/docs/GRAPH_ORCHESTRATION.md`

## 1. State Schema

```python
class ApplicationState(TypedDict):
    citizen_id: str
    scheme_id: str
    scheme_rules: dict
    required_documents: list
    collected_documents: list
    missing_documents: list
    eligibility_result: dict
    progress_log: list
```

## 2. All Nodes

- `requirement_agent`
- `vault_check`
- `department_fetch`
- `eligibility_engine`
- `notification_agent`

## 3. All Transitions
```python
workflow.set_entry_point("requirement_agent")
workflow.add_edge("requirement_agent", "vault_check")

workflow.add_conditional_edges(
    "vault_check",
    condition_function,
    {
        "fetch": "department_fetch",
        "eligible": "eligibility_engine"
    }
)

workflow.add_edge("department_fetch", "eligibility_engine")
workflow.add_edge("eligibility_engine", "notification_agent")
```

## 4. State Immutability Rule
Nodes must not mutate unrelated state fields.
Each node updates its specific designated keys in the `ApplicationState`.
