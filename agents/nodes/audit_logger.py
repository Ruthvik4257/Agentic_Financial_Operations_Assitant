import json
from typing import Dict, Any
from agents.state import AgentState
from backend.app.services.audit_service import AuditService
from backend.app.core.database import AsyncSessionLocal


async def audit_logger_node(state: AgentState) -> Dict[str, Any]:
    """
    Audit Logger Node:
    Appends a cryptographically verified SHA-256 event entry into the audit trail.
    """
    dispute = state["dispute"]
    policy_verdict = state.get("policy_verdict", "PENDING")
    execution_result = state.get("execution_result")
    
    justification = state.get("policy_reason") or "Audit state checkpoint recorded."
    action = f"STATE_{dispute.status}"
    if execution_result and execution_result.get("success"):
        action = "REFUND_EXECUTED"

    async with AsyncSessionLocal() as session:
        audit_entry = await AuditService.record_event(
            session=session,
            dispute_id=dispute.dispute_id,
            action=action,
            agent_node=state.get("current_node", "AuditLoggerNode"),
            justification=justification,
            state_diff={
                "status": dispute.status,
                "amount": dispute.amount,
                "fraud_score": state["fraud"].risk_score if state.get("fraud") else None,
                "execution_result": execution_result,
            },
        )

    return {
        "audit_hash": audit_entry.current_hash,
        "current_node": "AuditLoggerNode",
    }
