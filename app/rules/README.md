# `app/rules/`

This is VERY important.
You do not want eligibility logic mixed inside agents.

Example `eligibility_rules.py`:
```python
def check_income(citizen, rules):
    return citizen.income <= rules.income_limit
```

This keeps the system auditable and deterministic.
