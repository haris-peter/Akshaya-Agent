# `/docs/RULES_ENGINE_SPEC.md`

## 1. Rule Storage Format
```json
{
  "rule_id": "INC_LIMIT_2026",
  "description": "Income must not exceed 300000",
  "conditions": {
    "income": { "operator": "<=", "value": 300000 }
  }
}
```

## 2. Validation Strategy
- Load scheme rules via `scheme_id`.
- For each rule, validate against the `ApplicationState` profile context.
- If all conditions pass, eligibility passes.

## 3. Forbidden Actions
- Eligibility decision must not use language models.
- Department calls should not occur in the Rules Engine processing logic.

All eligibility decisions must be explainable via `rule_id` reference.
