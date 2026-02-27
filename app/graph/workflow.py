from langgraph.graph import StateGraph

from app.graph.state import ApplicationState
from app.graph.conditions import should_fetch_documents, check_eligibility_status

from app.tools.requirement_tool import requirement_tool
from app.tools.vault_tool import vault_tool
from app.tools.department_tool import department_agent as department_tool
from app.tools.eligibility_tool import eligibility_engine as eligibility_tool
from app.tools.explanation_tool import explanation_tool
from app.tools.notification_tool import notification_agent as notification_tool

workflow = StateGraph(ApplicationState)

workflow.add_node("requirement_tool", requirement_tool)
workflow.add_node("vault_tool", vault_tool)
workflow.add_node("department_tool", department_tool)
workflow.add_node("eligibility_tool", eligibility_tool)
workflow.add_node("explanation_tool", explanation_tool)
workflow.add_node("notification_tool", notification_tool)

workflow.set_entry_point("requirement_tool")

workflow.add_edge("requirement_tool", "vault_tool")

workflow.add_conditional_edges(
    "vault_tool",
    should_fetch_documents,
    {
        "fetch": "department_tool",
        "eligible": "eligibility_tool"
    }
)

workflow.add_edge("department_tool", "eligibility_tool")

workflow.add_conditional_edges(
    "eligibility_tool",
    check_eligibility_status,
    {
        "rejected": "explanation_tool",
        "approved": "explanation_tool"
    }
)

workflow.add_edge("explanation_tool", "notification_tool")

app_workflow = workflow.compile()
