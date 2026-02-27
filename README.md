# SaarthiAI: Autonomous Government Scheme Orchestration

SaarthiAI is a proof-of-concept AI-driven orchestration system designed to automate the evaluation, document retrieval, and intelligence of government scheme applications. Utilizing **LangGraph** for workflow orchestration, **FastAPI** for service exposure, and **PostgreSQL (NeonDB)** for persistence, the system acts as a multi-agent application pipeline.

## System Architecture

The core of the system is modeled as a state machine (`app/graph/workflow.py`) where specialized AI Agents process an application payload sequentially. 

![SaarthiAI Pipeline](docs/ARCHITECTURE.md)

### Agent Roles

1. **Requirement Agent (Policy Intelligence)**: Queries the database and policy matrices to identify exactly what documents a citizen needs to apply for a specific scheme.
2. **Vault Agent (Document Vault)**: Interrogates the citizen's existing document vault in PostgreSQL to check which of the required documents they already possess.
3. **Department Agent**: Intercepts missing documents and attempts to "fetch" or generate them dynamically by communicating with simulated external department APIs.
4. **Eligibility Engine**: A strict, deterministic Python rule-engine that guarantees policy compliance (e.g., checking if Annual Income is below limits). *No LLMs make deterministic decisions here!*
5. **Explanation Agent (LLM Integration)**: If an application is rejected, this LangChain node utilizes open-source models via OpenRouter (like `openrouter/auto`) to write a polite, customized explanation for the citizen.
6. **Notification Agent**: The terminal node that formats the structured approval/rejection payload and broadcasts it back to the client.

## Technologies Used

* **FastAPI**: Asynchronous web framework exposing the `/api/v1/apply` endpoint.
* **LangGraph**: State graph management for looping the application through specialized steps.
* **LangChain**: LLM integration and prompt templates for the Explanation Agent.
* **SQLAlchemy & asyncpg**: Fully asynchronous ORM integration with NeonDB (PostgreSQL).
* **OpenRouter**: LLM API gateway routing to free context models.

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Virtual Environment (`env`)
- PostgreSQL instance (NeonDB recommended)

### 2. Installation Setup
```bash
# Create and activate virtual environment
python -m venv env
.\env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (or use `.env.example` as a template):
```ini
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=openrouter/auto
DATABASE_URL=postgresql+asyncpg://user:password@host/neondb?ssl=require
```

### 4. Database Initialization
Seed the NeonDB instance with mock Scheme and Citizen data to test the LangGraph workflow:
```bash
python seed_db.py
```

### 4b. Policy and Admin Context Indexing (optional)
To index policy documents and the **Admin Panel context** for RAG (e.g. so the agent can answer questions about document types, requirements, and admin workflows), add `.txt`, `.md`, or `.pdf` files to the `policies/` folder and run:
```bash
python ingest_policies.py
```
The file `policies/admin_panel_context.md` is included and describes the Admin Panel tabs, API endpoints, and how the Citizen Portal uses admin-configured data. It is indexed with `doc_type=ADMIN`.

### 5. Running the Application
Start the Uvicorn web server in hot-reload mode:
```bash
python -m uvicorn main:app --port 8000 --reload
```

## Testing the Pipeline

Once the server is running, you can submit a test payload to trigger the entire orchestrator loop:

```bash
# Test API locally using the mock Citizen (C12345) and Scheme (GHS2024)
python test_api.py
```
*Alternatively, use `Invoke-RestMethod` in PowerShell or `curl` to POST to `http://127.0.0.1:8000/api/v1/apply`.* 

---
*Built with ❤️ for AI-Driven Governance.*