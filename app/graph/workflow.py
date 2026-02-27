from langgraph.graph import StateGraph

from app.graph.state import ApplicationState
from app.graph.conditions import should_fetch_documents, check_eligibility_status

from app.agents.requirement_agent import requirement_agent
from app.agents.vault_agent import vault_agent
from app.agents.department_agent import department_agent
from app.agents.eligibility_engine import eligibility_engine
from app.agents.explanation_agent import explanation_agent
from app.agents.notification_agent import notification_agent

# Initialize the StateGraph
workflow = StateGraph(ApplicationState)

# Add all nodes (agents)
workflow.add_node("requirement_agent", requirement_agent)
workflow.add_node("vault_check", vault_agent)
workflow.add_node("department_fetch", department_agent)
workflow.add_node("eligibility_engine", eligibility_engine)
workflow.add_node("explanation_agent", explanation_agent)
workflow.add_node("notification_agent", notification_agent)

# Define entry point
workflow.set_entry_point("requirement_agent")

# Add edges based on logic
workflow.add_edge("requirement_agent", "vault_check")

# Conditional: Do we need to fetch documents from departments?
workflow.add_conditional_edges(
    "vault_check",
    should_fetch_documents,
    {
        "fetch": "department_fetch",
        "eligible": "eligibility_engine"
    }
)

# After fetching documents, check eligibility
workflow.add_edge("department_fetch", "eligibility_engine")

# Conditional: Was the user approved or rejected?
workflow.add_conditional_edges(
    "eligibility_engine",
    check_eligibility_status,
    {
        "rejected": "explanation_agent",
        "approved": "notification_agent"
    }
)

# If rejected, after getting an explanation, notify the user
workflow.add_edge("explanation_agent", "notification_agent")

# Compile the final graph
app_workflow = workflow.compile()
