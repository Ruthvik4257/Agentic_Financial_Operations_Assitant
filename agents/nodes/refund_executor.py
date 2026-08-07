from datetime import datetime, timezone
from typing import Dict, Any
from agents.state import AgentState
from backend.app.schemas.erp import ERPPaymentEntryCreate, ERPPaymentEntryReference
from backend.app.services.erpnext_mock import get_erp_client


async def refund_executor_node(state: AgentState) -> Dict[str, Any]:
    """
    Refund Executor Node:
    Calls ERPNext REST API to post a negative Payment Entry (Refund)
    linked to the disputed Sales Invoice.
    """
    client = get_erp_client()
    dispute = state["dispute"]
    erp_invoice = state.get("erp_invoice") or {}
    
    # Mathematical guardrail: Clamp refund amount to invoice total
    invoice_total = erp_invoice.get("grand_total", dispute.amount)
    safe_refund_amount = min(dispute.amount, invoice_total)

    payload = ERPPaymentEntryCreate(
        payment_type="Pay",
        party_type="Customer",
        party=dispute.customer_id,
        paid_amount=safe_refund_amount,
        received_amount=safe_refund_amount,
        reference_no=f"REFUND-{dispute.dispute_id}",
        reference_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        paid_from="1110 - Bank Account - TC",
        paid_to="2110 - Debtors - TC",
        references=[
            ERPPaymentEntryReference(
                reference_doctype="Sales Invoice",
                reference_name=dispute.invoice_id,
                allocated_amount=safe_refund_amount,
            )
        ],
        remarks=f"Autonomous AI Refund: {dispute.reason}",
    )

    result = await client.create_refund_payment(payload)
    dispute.status = "EXECUTED"

    return {
        "execution_result": {
            "success": True,
            "payment_entry_id": result.get("name"),
            "refund_amount": safe_refund_amount,
            "status": "Submitted",
            "posting_date": result.get("posting_date"),
        },
        "dispute": dispute,
        "current_node": "RefundExecutorNode",
    }
