from typing import Dict, Any, List

OPERATORS = {
    "<":  lambda a, b: a is not None and a < b,
    "<=": lambda a, b: a is not None and a <= b,
    ">":  lambda a, b: a is not None and a > b,
    ">=": lambda a, b: a is not None and a >= b,
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

def evaluate_rule(profile: Dict[str, Any], rule: Dict[str, Any]) -> tuple[bool, str]:
    """
    Evaluates a single rule against the citizen profile.
    Returns (passed: bool, reason: str).
    """
    field = rule.get("field")
    op = rule.get("operator")
    value = rule.get("value")
    label = rule.get("label", f"{field} {op} {value}")
    
    operator_fn = OPERATORS.get(op)
    if not operator_fn:
        return False, f"Unknown operator '{op}' in rule for field '{field}'."
    
    citizen_value = profile.get(field)
    passed = operator_fn(citizen_value, value)
    
    if not passed:
        return False, label
    return True, ""


def evaluate_rules(profile: Dict[str, Any], rules_json: Dict[str, Any]) -> tuple[bool, str]:
    """
    Generic rule interpreter. Supports:
    - all_of: ALL rules must pass (AND logic)
    - any_of: AT LEAST ONE rule must pass (OR logic)
    - none_of: NO rules must pass (NOT logic)

    Rules can be nested. Returns (passed: bool, reason: str).
    """
    if not rules_json:
        return True, ""

    # --- all_of (AND logic) ---
    for rule in rules_json.get("all_of", []):
        if "all_of" in rule or "any_of" in rule or "none_of" in rule:
            passed, reason = evaluate_rules(profile, rule)
        else:
            passed, reason = evaluate_rule(profile, rule)
        if not passed:
            return False, reason

    # --- any_of (OR logic) ---
    any_of_rules = rules_json.get("any_of", [])
    if any_of_rules:
        any_passed = False
        any_fail_reasons = []
        for rule in any_of_rules:
            if "all_of" in rule or "any_of" in rule or "none_of" in rule:
                passed, reason = evaluate_rules(profile, rule)
            else:
                passed, reason = evaluate_rule(profile, rule)
            if passed:
                any_passed = True
                break
            any_fail_reasons.append(reason)
        if not any_passed:
            return False, "None of the required conditions met: " + "; ".join(any_fail_reasons)

    # --- none_of (NOT logic) ---
    for rule in rules_json.get("none_of", []):
        if "all_of" in rule or "any_of" in rule or "none_of" in rule:
            passed, _ = evaluate_rules(profile, rule)
        else:
            passed, _ = evaluate_rule(profile, rule)
        if passed:
            return False, rule.get("label", "A disqualifying condition was met.")

    return True, ""
