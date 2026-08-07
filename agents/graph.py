from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes.supervisor import supervisor_node
from agents.nodes.investigator import investigator_node
from agents.nodes.fraud_analyst import fraud_analyst_node
from agents.nodes.policy_gatekeeper import policy_gatekeeper_node
from agents.nodes.refund_executor import refund_executor_node
from agents.nodes.audit_logger import audit_logger_node


def route_policy(state: AgentState) -> Literal["refund_executor", "audit_logger", "__end__"]:
    verdict = state.get("policy_verdict")
    if verdict == "AUTO_APPROVE":
        return "refund_executor"
    elif verdict == "REQUIRE_HITL":
        return "__end__" # Pauses for Human-in-the-Loop manager approval
    else:
        return "audit_logger" # Auto reject path


def build_financial_agent_graph():
    """
    Constructs the Enterprise FinOps LangGraph State Machine.
    """
    builder = StateGraph(AgentState)

    # 1. Add all functional nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("investigator", investigator_node)
    builder.add_node("fraud_analyst", fraud_analyst_node)
    builder.add_node("policy_gatekeeper", policy_gatekeeper_node)
    builder.add_node("refund_executor", refund_executor_node)
    builder.add_node("audit_logger", audit_logger_node)

    # 2. Linear pipeline edges
    builder.set_entry_point("supervisor")
    builder.add_edge("supervisor", "investigator")
    builder.add_edge("investigator", "fraud_analyst")
    builder.add_edge("fraud_analyst", "policy_gatekeeper")

    # 3. Conditional governance routing
    builder.add_conditional_edges(
        "policy_gatekeeper",
        route_policy,
        {
            "refund_executor": "refund_executor",
            "audit_logger": "audit_logger",
            "__end__": END,
        },
    )

    # 4. Post-execution logging
    builder.add_edge("refund_executor", "audit_logger")
    builder.add_edge("audit_logger", END)

    return builder.compile()


finops_agent = build_financial_agent_graph()
