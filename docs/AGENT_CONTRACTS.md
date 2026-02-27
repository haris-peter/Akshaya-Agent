# `/docs/AGENT_CONTRACTS.md`

## 1. Requirement Agent
**Inputs:** `scheme_id`, `citizen_profile`
**Outputs:** `required_documents`, `scheme_rules`
**Responsibility:** Determine the set of documents required for the citizen to apply.
**Forbidden:** No database calls; read constraints from passed state.

## 2. Document Vault Agent
**Inputs:** `citizen_id`, `required_documents`
**Outputs:** `collected_documents`, `missing_documents`
**Responsibility:** Check existing citizen documents for validity in the vault.
**Forbidden:** Do not fetch external documents.

## 3. Department Fetch Agent
**Inputs:** `citizen_id`, `missing_documents`
**Outputs:** Append to `collected_documents`, clear `missing_documents`
**Responsibility:** Interface with department agents to acquire missing documents.
**Forbidden:** Do not perform eligibility checks based on fetched data.

## 4. Eligibility Engine
**Inputs:** `citizen_id`, `scheme_rules`, `collected_documents`
**Outputs:** `eligibility_result` (Approval/Rejection object)
**Responsibility:** Deterministic validation against rules.
**Forbidden:** No LLM logic. Pure code rules.

## 5. Explanation Agent
**Inputs:** `eligibility_result.reason`
**Outputs:** Explanation string based on policy
**Responsibility:** Use RAG over policy documents to clarify why an application was rejected.
**Forbidden:** Must not change the eligibility status.
