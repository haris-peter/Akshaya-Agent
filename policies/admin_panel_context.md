# Admin Panel Context — SaarthiAI Akshaya-Agent

This document describes the Admin Panel and related API so that the agent can answer questions about configuration, document types, requirements, and administration workflows.

## Overview

The SaarthiAI application has two main entry points in the Streamlit UI: **Citizen Portal** and **Admin Panel**. The Admin Panel is used to manage document types and their requirements. It is implemented in `streamlit_app.py` and talks to the FastAPI backend at `http://127.0.0.1:8000`.

## Admin Panel Location and Navigation

- The Admin Panel is rendered by the function `admin_page()` in `streamlit_app.py`.
- Users switch between "Citizen Portal" and "Admin Panel" via a sidebar radio button.
- When "Admin Panel" is selected, `admin_page()` runs and shows the heading "Admin Panel" and the description "Manage document types and their requirements."

## Admin Panel Tabs

The Admin Panel has three tabs:

### Tab 1: Document Types

- **Purpose:** View all configured document types and their nested requirements.
- **Data:** Fetched via `GET /api/v1/document-types`. For each document type, requirements are fetched with `GET /api/v1/requirements/by-type/{document_type_id}`.
- **UI:** Each document type is shown in an expander with name and slug (e.g. "Land Records · `land`"). Optional description is shown. Under each type, each requirement is listed with:
  - Name
  - Mandatory (red) or Optional (yellow)
  - OCR mode: "LLM Vision" or "Tesseract"
  - A delete button (trash) that calls `DELETE /api/v1/requirements/{req_id}`.
- **Delete document type:** Each type has a "Delete Type" button that calls `DELETE /api/v1/document-types/{dt_id}`. Deleting a type removes it and all its requirements.
- If there are no document types, a message says to add one in the "Add Document Type" tab.

### Tab 2: Requirements

- **Purpose:** Add a new requirement to an existing document type.
- **Data:** Document types list from `GET /api/v1/document-types`.
- **Form fields:**
  - Document Type (required) — dropdown of existing types.
  - Requirement Name (required) — e.g. "Aadhar Card".
  - OCR Mode — "tesseract" (text/scanned docs) or "llm_vision" (blueprints/images).
  - Mandatory — checkbox, default True.
- **Submit:** On "Add Requirement", the app calls `POST /api/v1/requirements` with payload: `document_type_id`, `name`, `ocr_mode`, `is_mandatory`.
- If no document types exist, the user is told to add a document type first.

### Tab 3: Add Document Type

- **Purpose:** Create a new document type.
- **Form fields:**
  - Document Type Name (required) — e.g. "Land Records".
  - Slug (required) — e.g. "land" (lowercase, no spaces). Stored as lowercase with spaces replaced by underscores.
  - Description (optional) — text area.
- **Submit:** On "Add Document Type", the app calls `POST /api/v1/document-types` with payload: `name`, `slug`, `description`.
- After creation, the user is told to add requirements in the Requirements tab.

## API Endpoints Used by the Admin Panel

All base URL: `API_BASE = "http://127.0.0.1:8000"` (in streamlit_app.py).

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/document-types | List all document types (id, name, slug, description). |
| POST | /api/v1/document-types | Create document type (body: name, slug, description). |
| DELETE | /api/v1/document-types/{dt_id} | Delete a document type and its requirements. |
| GET | /api/v1/requirements | List all requirements with document type info. |
| GET | /api/v1/requirements/by-type/{document_type_id} | List requirements for one document type. |
| POST | /api/v1/requirements | Add requirement (body: document_type_id, name, ocr_mode, is_mandatory). |
| DELETE | /api/v1/requirements/{req_id} | Delete a requirement. |

## Backend Models (Database)

- **DocumentType:** id, name (unique), slug (unique), description, timestamps. Has relationship to Requirement (cascade delete).
- **Requirement:** id, document_type_id (FK to document_type), name, ocr_mode (default "tesseract"), is_mandatory (default True), timestamps. Belongs to one DocumentType; document_type is accessed via relationship `doc_type`.

## How the Citizen Portal Uses Admin-Configured Data

- The Citizen Portal lists document types from `GET /api/v1/document-types` for the "Document Request Type" dropdown.
- After the user selects a type and enters Aadhar and clicks "Check Requirements", the app loads requirements with `GET /api/v1/requirements/by-type/{document_type_id}` and shows file uploaders (one per requirement, labeled mandatory or optional).
- If a document type has no requirements, the message says: "No configured requirements found for doc type 'X'. Add from the Admin Panel."
- If there are no document types at all, the message says: "No document types available. Please ask the admin to configure them."

## Async and Run Helpers

- The Streamlit app uses async API helpers (e.g. `get_document_types_api()`, `get_requirements_by_type_api()`, `add_document_type_api()`, `delete_document_type_api()`, `add_requirement_api()`, `delete_requirement_api()`).
- These are run via `run_async(coro)` which handles asyncio event loop (including when a loop is already running).

## Summary for the Agent

- The Admin Panel manages **document types** (name, slug, description) and **requirements** (name, ocr_mode, is_mandatory) per type.
- All admin operations go through the FastAPI routes under `/api/v1` for document-types and requirements.
- The Citizen Portal depends on document types and requirements being configured in the Admin Panel; without them, citizens see clear messages directing them to admin configuration.
