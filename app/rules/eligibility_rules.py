from typing import Dict, Any

# Mock Database of Scheme Rules
# In reality, this is loaded from PostgreSQL Scheme Models.
MOCK_SCHEME_RULES = {
    "GHS": {
        "scheme_id": "GHS",
        "name": "Gramin Housing Scheme",
        "income_limit": 300000,
        "district_required": True,
        "documents": [
            "income_certificate",
            "caste_certificate",
            "land_record"
        ],
        "conditional_documents": {
            "if_category_SC_ST": ["community_certificate"],
        }
    },
    "GHS2024": {
        "documents": [
            "Aadhar Card",
            "income_certificate",
            "medical_certificate"
        ]
    }
}

def check_income(citizen_income: int, income_limit: int) -> bool:
    return citizen_income <= income_limit

def get_scheme_rules(scheme_id: str) -> Dict[str, Any]:
    """Retrieves rules for the designated scheme."""
    return MOCK_SCHEME_RULES.get(scheme_id, {})
