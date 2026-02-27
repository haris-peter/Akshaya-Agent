from typing import TypedDict, List, Dict, Any, Optional

class DocumentState(TypedDict):
    aadhar_number: str
    document_request_type: str
    citizen: Dict[str, Any]
    tracking_id: Optional[int]
    requirements: List[Dict[str, Any]]
    uploaded_files: Dict[str, bytes]
    vault_summaries: Dict[str, str]
    compliance_report: Dict[str, Any]
    status: str
    progress_log: List[str]
