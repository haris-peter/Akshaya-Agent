# `/docs/ARCHITECTURE.md`

# SaarthiAI – Autonomous Government Scheme Orchestration System

## 1. System Overview
SaarthiAI is a multi-agent orchestration system designed to automate government scheme application workflows through intelligent agent coordination.
The system enables a citizen to apply for a government scheme with a single action while autonomous agents:
- Identify required documents
- Retrieve missing documents from relevant departments
- Validate eligibility deterministically
- Provide explainable approval or rejection
- Maintain transparent real-time progress

## 2. Core Philosophy

### 2.1 Design Principles
1. **Documents should not travel with citizens. Agents should travel to documents.**
2. Eligibility decisions must be deterministic and auditable.
3. LLMs may explain decisions but must never determine eligibility.
4. All state transitions must be logged.
5. Each agent has a single responsibility.
6. Orchestration logic must be separated from business logic.
7. All agent communication must follow structured contracts.

## 3. High-Level Architecture

```text
Citizen Portal
      ↓
FastAPI Application Layer
      ↓
LangGraph Orchestrator
      ↓
┌──────────────────────────────────────────┐
│                                          │
│   Requirement Agent                      │
│   Document Vault Agent                   │
│   Department Fetch Agents                │
│   Eligibility Engine (Deterministic)     │
│   Explanation Agent (RAG)                │
│   Notification Agent                     │
│                                          │
└──────────────────────────────────────────┘
      ↓
Decision + Progress Stream
```

## 4. System Layers

### 4.1 API Layer (FastAPI)
Responsibilities:
- Expose public endpoints
- Accept application requests
- Stream progress updates via WebSocket
- Invoke LangGraph workflow
- Return final structured response

The API layer must:
- Contain no business logic
- Contain no eligibility logic
- Not directly call department services
- Only delegate to orchestration layer

### 4.2 Orchestration Layer (LangGraph)
This is the workflow engine.

Responsibilities:
- Maintain application state
- Route execution between agents
- Handle conditional branching
- Control retries and failures
- Emit progress updates

The Orchestrator must:
- Not contain eligibility rules
- Not contain LLM prompts
- Not contain database logic
- Only coordinate agents

### 4.3 Agent Layer
Each agent performs one well-defined task.

Agents must:
- Accept `ApplicationState`
- Return updated `ApplicationState`
- Not mutate unrelated state fields
- Not contain orchestration logic

**Core Agents**
1. **Requirement Agent**: Determines required documents and loads scheme rules.
2. **Document Vault Agent**: Checks existing citizen documents for validity.
3. **Department Fetch Agents**: Retrieve missing documents from simulated department systems.
4. **Eligibility Engine**: Applies deterministic rule validation.
5. **Explanation Agent**: Uses RAG to generate policy-based explanations.
6. **Notification Agent**: Produces structured output for citizen.

### 4.4 Rules Engine (Deterministic Core)
The rules engine is the authoritative decision layer.

Characteristics:
- Fully deterministic
- Versioned rule definitions
- Referenceable rule IDs
- Audit-friendly

LLMs must never override or alter rule outcomes. Eligibility decisions must be explainable using rule references.

### 4.5 RAG Layer (Policy Knowledge Layer)
Purpose:
- Provide explanation support
- Retrieve official scheme clauses
- Generate structured explanations

RAG is used only for:
- Justifying rejection
- Explaining document requirements
- Answering citizen queries

RAG must not:
- Decide eligibility
- Modify rule outcomes
- Generate new rule interpretations

### 4.6 Department Simulation Layer
Each department behaves as a separate logical service.

Examples:
- Revenue Department
- Tax Department
- Land Registry

Each department exposes:
- Structured API contract
- Deterministic document generation
- Standardized error responses

Departments must not:
- Contain eligibility logic
- Modify scheme rules

### 4.7 Data Layer
Core entities:
- Citizen
- Scheme
- Application
- DocumentVault
- Department Records

Data layer responsibilities:
- Maintain referential integrity
- Enforce constraints
- Support audit logging

Business logic must not be embedded inside database models.

## 5. Application State Model
All workflow execution revolves around a single structured state object.

Example structure:
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

State Rules:
- State must be serializable.
- State mutations must be controlled.
- Each agent must update only its relevant fields.
- Progress log must be appended, never overwritten.

## 6. Workflow Overview
```text
START
      ↓
Requirement Agent
      ↓
Vault Check Agent
      ↓
If Missing Documents:
   → Department Fetch Agents
      ↓
Eligibility Engine
      ↓
If Rejected:
   → Explanation Agent
      ↓
Notification Agent
      ↓
END
```

## 7. Progress Tracking Model
Every agent must emit:
- Start event
- Completion event
- Failure event (if applicable)

Allowed statuses:
- pending
- in_progress
- completed
- failed

Progress events must be:
- Structured JSON
- Streamable via WebSocket

## 8. Non-Negotiable Constraints
1. LLMs must never decide eligibility.
2. Rules engine must remain deterministic.
3. Orchestrator must not contain business logic.
4. Agents must not call each other directly.
5. All external service calls must use defined contracts.
6. All decisions must be explainable.
7. All errors must be logged.
8. System must operate using dummy data only (prototype constraint).

## 9. Scalability Considerations
Future expansion may include:
- Multi-state rule engines
- Real department integrations
- Fraud detection agent
- Application revalidation workflows
- Role-based administrative dashboards
- Kubernetes deployment

Architecture must remain modular to support microservice separation.

## 10. Security Considerations
- No real Aadhaar usage
- Mock data only
- Input validation required at API layer
- All agent outputs must be validated
- Document vault must enforce access control

## 11. Versioning Strategy
- Scheme rules must be versioned
- Rule updates must not retroactively affect past applications
- Eligibility decisions must reference rule version ID
- Workflow versioning must be documented

## 12. Summary
SaarthiAI is a structured, explainable, deterministic, multi-agent orchestration system designed to simulate autonomous government scheme application processing.

The architecture ensures:
- Clear separation of concerns
- Deterministic eligibility decisions
- Controlled use of LLMs
- Transparent progress tracking
- Extensibility for real-world scaling

This document serves as the foundational governance blueprint for all system development.
