from typing import Dict, Any
from agents.state import AgentState
from agents.models.llm_factory import llm_client


async def fraud_analyst_node(state: AgentState) -> Dict[str, Any]:
    """
    Fraud Analyst Node:
    Runs deep forensic accounting reasoning via Gemini to score fraud risk
    and verify duplicate ledger records in ERPNext.
    """
    dispute = state["dispute"]
    erp_invoice = state.get("erp_invoice")
    erp_payments = state.get("erp_payments")
    customer_profile = state.get("customer_profile")

    fraud_assessment = await llm_client.analyze_dispute(
        customer_id=dispute.customer_id,
        invoice_id=dispute.invoice_id,
        amount=dispute.amount,
        dispute_reason=dispute.reason,
        erp_invoice=erp_invoice,
        erp_payments=erp_payments,
        customer_profile=customer_profile,
    )

    return {
        "fraud": fraud_assessment,
        "current_node": "FraudAnalystNode",
    }
