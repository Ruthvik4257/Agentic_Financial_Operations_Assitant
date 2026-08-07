from typing import Dict, Any
from agents.state import AgentState, DisputeRecord
from agents.models.fast_classifier import FastEntityExtractor


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor Node: Extracts entities, normalizes customer message,
    and sets up initial dispute context for the LangGraph pipeline.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]["content"] if messages else ""
    
    extracted = FastEntityExtractor.extract_entities(last_message)
    existing_dispute = state.get("dispute")
    
    invoice_id = extracted.get("invoice_id") or (existing_dispute.invoice_id if existing_dispute else "INV-2026-001")
    amount = extracted.get("amount") or (existing_dispute.amount if existing_dispute else 150.0)
    customer_id = existing_dispute.customer_id if existing_dispute else "CUST-001"
    dispute_id = existing_dispute.dispute_id if existing_dispute else f"DISP-{invoice_id}"
    reason = last_message or (existing_dispute.reason if existing_dispute else "Customer dispute")

    dispute = DisputeRecord(
        dispute_id=dispute_id,
        customer_id=customer_id,
        invoice_id=invoice_id,
        amount=amount,
        currency="USD",
        reason=reason,
        status="PENDING_INVESTIGATION",
    )

    return {
        "dispute": dispute,
        "current_node": "SupervisorNode",
    }
