# `app/api/`

This folder contains the FastAPI entry point for the application.

Responsibilities:
- Expose public endpoints for the citizen portal
- Allow citizens to submit applications
- Expose WebSocket/SSE endpoints for real-time progress tracking

Constraints:
- **No business logic**: Must delegate all logic to the orchestration or rules layer.
- **No direct DB calls**: Use dependency injection or service layers.

Example Routes:
- `POST /apply/{scheme_id}`: Trigger the LangGraph workflow.
- `GET /schemes`: List available schemes.
- `WS /progress/{application_id}`: Stream Live progress updates.
