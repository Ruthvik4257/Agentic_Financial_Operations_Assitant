from typing import Dict, Any
from agents.state import AgentState, DisputeRecord
from agents.models.fast_classifier import FastEntityExtractor


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor Node: Extracts entities via Hugging Face Financial helper models,
    normalizes customer message, and polymorphically sets up dispute context.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]["content"] if messages else ""
    
    extracted = FastEntityExtractor.extract_entities(last_message)
    existing = state.get("dispute")
    
    # Polymorphic access whether pydantic or SQLAlchemy
    ext_id = getattr(existing, 'id', getattr(existing, 'dispute_id', None))
    ext_inv = getattr(existing, 'invoice_id', None)
    ext_amt = getattr(existing, 'amount', None)
    ext_cust = getattr(existing, 'customer_id', 'CUST-001')
    ext_reason = getattr(existing, 'reason', last_message)

    amount = extracted.get("amount") or ext_amt or 200.0
    invoice_id = extracted.get("invoice_id") or ext_inv or (f"INV-2026-{int(amount)}" if amount else "INV-2026-001")
    dispute_id = ext_id or f"DISP-{invoice_id}"
    customer_id = ext_cust or "CUST-001"
    reason = last_message or ext_reason or "Customer payment dispute"

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

