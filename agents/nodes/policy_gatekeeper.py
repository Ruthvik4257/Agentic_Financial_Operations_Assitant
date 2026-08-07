from typing import Dict, Any
from backend.app.core.config import settings
from agents.state import AgentState


async def policy_gatekeeper_node(state: AgentState) -> Dict[str, Any]:
    """
    Policy Gatekeeper Node:
    Enforces deterministic corporate financial governance and risk thresholds.
    Strictly protects against prompt injections and unauthorized money movement.
    """
    dispute = state["dispute"]
    fraud = state.get("fraud")
    erp_invoice = state.get("erp_invoice")

    if not erp_invoice:
        return {
            "policy_verdict": "AUTO_REJECT",
            "policy_reason": f"Invoice {dispute.invoice_id} could not be verified in ERPNext.",
            "current_node": "PolicyGatekeeper",
        }

    risk_score = fraud.risk_score if fraud else 0.50
    amount = dispute.amount

    if risk_score >= 0.85:
        verdict = "AUTO_REJECT"
        reason = f"High anomaly fraud risk score ({risk_score:.2f}) exceeded critical security ceiling."
    elif amount < settings.MAX_AUTO_REFUND_LIMIT and risk_score <= settings.MAX_FRAUD_RISK_THRESHOLD:
        verdict = "AUTO_APPROVE"
        reason = f"Dispute amount (${amount:.2f}) and Risk Score ({risk_score:.2f}) within autonomous policy thresholds."
    else:
        verdict = "REQUIRE_HITL"
        reason = f"Dispute requires Human-in-the-Loop manager authorization (Amount: ${amount:.2f}, Risk: {risk_score:.2f})."

    return {
        "policy_verdict": verdict,
        "policy_reason": reason,
        "current_node": "PolicyGatekeeper",
    }
