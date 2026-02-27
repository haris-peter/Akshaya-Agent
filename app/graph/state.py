from typing import TypedDict, List, Dict, Any

class ApplicationState(TypedDict):
    """
    Represents the state of a government scheme application as it flows through the system.
    """
    citizen_id: str
    scheme_id: str
    scheme_rules: Dict[str, Any]
    required_documents: List[str]
    collected_documents: List[str]
    missing_documents: List[str]
    eligibility_result: Dict[str, Any]
    progress_log: List[Dict[str, Any]]
