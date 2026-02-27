# `/docs/DEPARTMENT_PROTOCOL.md`

This defines how inter-agency agents communicate.
Each department behaves as a separate microservice.

## 1. Standard Request Format
```json
POST /generate-document
{
  "citizen_id": "1234567890",
  "document_type": "income_certificate"
}
```

## 2. Standard Response Format
```json
{
  "status": "success",
  "document_id": "DOC-89028340",
  "issued_at": "2026-03-01T12:00:00Z"
}
```

## 3. Allowed Operations
- `POST /generate-document`
- `GET /verify-document`

## 4. Timeout Handling
- Define strict timeouts for inter-service RPC calls (e.g. 5 seconds max).
- Retry policy: Max 3 retries with exponential backoff.

## 5. Error Codes
- `400`: Invalid Request format
- `404`: Citizen record not found
- `500`: Internal Department Error
- `503`: Department Service Unavailable
