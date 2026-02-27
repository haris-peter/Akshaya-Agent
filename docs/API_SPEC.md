# `/docs/API_SPEC.md`

## 1. Core Endpoints
- `POST /apply/{scheme_id}`
- `GET /schemes`
- `GET /application/{application_id}`

## 2. WebSocket/SSE Progress Tracker
- `WS /progress/{application_id}`

Event Payload Example:
```json
{
  "step": "department_fetch",
  "status": "in_progress",
  "message": "Fetching income certificate"
}
```

## 3. Streaming Flow
1. Citizen calls `/apply` with payload.
2. System immediately returns `application_id`.
3. Citizen opens WebSocket to `/progress/{application_id}`.
4. Orchestrator pushes real-time events to the frontend.
5. On completion, emission of `status: "completed"` with URL to download generated document.
