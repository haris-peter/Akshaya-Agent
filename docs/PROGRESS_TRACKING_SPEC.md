# `/docs/PROGRESS_TRACKING_SPEC.md`

## 1. Event Emission Rules
Every agent must emit at least:
- `start` event
- `completion` event
- `failure` event (if applicable)

## 2. Event Lifecycle
```json
{
    "application_id": "APP-2026",
    "agent": "department_fetch",
    "step": "Connecting to Revenue Department",
    "status": "in_progress",
    "timestamp": "2026-03-01T12:05:00Z"
}
```

## 3. Allowed States
- `pending`
- `in_progress`
- `completed`
- `failed`

## 4. Progress Events Core Constraints
- Must be Structured JSON.
- Streamable via WebSocket securely to the frontend.
- Provide progressive transparency into the "black box" of agent operations.
