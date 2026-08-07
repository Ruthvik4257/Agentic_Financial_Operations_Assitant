from typing import Dict, Any
from agents.state import AgentState
from backend.app.services.erpnext_mock import get_erp_client


async def investigator_node(state: AgentState) -> Dict[str, Any]:
    """
    Payment Investigator Node:
    Queries ERPNext for Sales Invoice, linked Payment Entries, and Customer details.
    """
    client = get_erp_client()
    dispute = state["dispute"]
    invoice_id = dispute.invoice_id

    invoice = await client.get_invoice(invoice_id)
    customer_id = invoice.get("customer", dispute.customer_id) if invoice else dispute.customer_id
    
    payments = await client.get_payment_entries_for_invoice(invoice_id)
    customer = await client.get_customer(customer_id)

    return {
        "erp_invoice": invoice,
        "erp_payments": payments,
        "customer_profile": customer,
        "current_node": "InvestigatorNode",
    }
