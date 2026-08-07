import copy
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.schemas.erp import ERPPaymentEntryCreate
from backend.app.services.erpnext_client import BaseERPNextClient, LiveERPNextClient


class EmbeddedERPNextEngine(BaseERPNextClient):
    """
    High-fidelity in-memory ERPNext simulator mirroring the Frappe v14/v15 DocType schemas
    and standard REST endpoints. Guarantees 100% offline hackathon and demo resilience.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._customers = {
            "CUST-001": {
                "name": "CUST-001",
                "customer_name": "Acme Corporation",
                "customer_group": "Enterprise Commercial",
                "territory": "United States",
                "credit_limit": 50000.00,
                "loyalty_tier": "Platinum",
                "total_invoiced": 128450.00,
                "lifetime_chargebacks": 0,
            },
            "CUST-002": {
                "name": "CUST-002",
                "customer_name": "Globex Logistics Corp",
                "customer_group": "Global Logistics",
                "territory": "North America",
                "credit_limit": 25000.00,
                "loyalty_tier": "Gold",
                "total_invoiced": 42100.00,
                "lifetime_chargebacks": 1,
            },
            "CUST-003": {
                "name": "CUST-003",
                "customer_name": "Initech Software Labs",
                "customer_group": "SMB Software",
                "territory": "United Kingdom",
                "credit_limit": 10000.00,
                "loyalty_tier": "Silver",
                "total_invoiced": 8500.00,
                "lifetime_chargebacks": 0,
            },
        }

        self._invoices = {
            "INV-2026-001": {
                "name": "INV-2026-001",
                "customer": "CUST-001",
                "customer_name": "Acme Corporation",
                "posting_date": "2026-08-01",
                "due_date": "2026-08-31",
                "grand_total": 150.00,
                "outstanding_amount": 0.00,
                "status": "Paid",
                "currency": "USD",
                "items": [
                    {
                        "item_code": "CLOUD-OPS-SEAT",
                        "item_name": "Cloud Operations Seat License",
                        "qty": 1.0,
                        "rate": 150.0,
                        "amount": 150.0,
                    }
                ],
            },
            "INV-2026-045": {
                "name": "INV-2026-045",
                "customer": "CUST-001",
                "customer_name": "Acme Corporation",
                "posting_date": "2026-08-03",
                "due_date": "2026-09-02",
                "grand_total": 850.00,
                "outstanding_amount": 0.00,
                "status": "Paid",
                "currency": "USD",
                "items": [
                    {
                        "item_code": "ENTERPRISE-SUPPORT",
                        "item_name": "Enterprise Dedicated FinOps Support",
                        "qty": 1.0,
                        "rate": 850.0,
                        "amount": 850.0,
                    }
                ],
            },
            "INV-2026-102": {
                "name": "INV-2026-102",
                "customer": "CUST-002",
                "customer_name": "Globex Logistics Corp",
                "posting_date": "2026-08-05",
                "due_date": "2026-09-05",
                "grand_total": 2500.00,
                "outstanding_amount": 0.00,
                "status": "Paid",
                "currency": "USD",
                "items": [
                    {
                        "item_code": "LOGISTICS-API-BANDWIDTH",
                        "item_name": "Logistics API High-Throughput Tier",
                        "qty": 1.0,
                        "rate": 2500.0,
                        "amount": 2500.0,
                    }
                ],
            },
            "INV-2026-999": {
                "name": "INV-2026-999",
                "customer": "CUST-003",
                "customer_name": "Initech Software Labs",
                "posting_date": "2026-08-07",
                "due_date": "2026-08-21",
                "grand_total": 45.00,
                "outstanding_amount": 45.00,
                "status": "Unpaid",
                "currency": "USD",
                "items": [
                    {
                        "item_code": "API-STORAGE-OVERAGE",
                        "item_name": "Storage Overage Surcharge",
                        "qty": 1.0,
                        "rate": 45.0,
                        "amount": 45.0,
                    }
                ],
            },
        }

        self._payments = {
            "PE-2026-001A": {
                "name": "PE-2026-001A",
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": "CUST-001",
                "paid_amount": 150.00,
                "received_amount": 150.00,
                "reference_no": "TX-SETTLE-8821",
                "reference_date": "2026-08-01",
                "status": "Submitted",
                "posting_date": "2026-08-01",
                "references": [{"reference_doctype": "Sales Invoice", "reference_name": "INV-2026-001", "allocated_amount": 150.00}],
                "remarks": "Credit Card Settlement - Stripe Batch #992",
            },
            "PE-2026-001B": {
                "name": "PE-2026-001B",
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": "CUST-001",
                "paid_amount": 150.00,
                "received_amount": 150.00,
                "reference_no": "TX-SETTLE-8821-DUP",
                "reference_date": "2026-08-01",
                "status": "Submitted",
                "posting_date": "2026-08-01",
                "references": [{"reference_doctype": "Sales Invoice", "reference_name": "INV-2026-001", "allocated_amount": 150.00}],
                "remarks": "Duplicate gateway capture anomaly #992-DUP",
            },
            "PE-2026-045A": {
                "name": "PE-2026-045A",
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": "CUST-001",
                "paid_amount": 850.00,
                "received_amount": 850.00,
                "reference_no": "TX-WIRE-9912",
                "reference_date": "2026-08-03",
                "status": "Submitted",
                "posting_date": "2026-08-03",
                "references": [{"reference_doctype": "Sales Invoice", "reference_name": "INV-2026-045", "allocated_amount": 850.00}],
                "remarks": "Automated ACH Settlement - Chase Commercial",
            },
        }

    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        inv = self._invoices.get(invoice_id)
        return copy.deepcopy(inv) if inv else None

    async def list_invoices_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        return [copy.deepcopy(inv) for inv in self._invoices.values() if inv.get("customer") == customer_id]

    async def get_payment_entries_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        matching = []
        for pe in self._payments.values():
            for ref in pe.get("references", []):
                if ref.get("reference_name") == invoice_id:
                    matching.append(copy.deepcopy(pe))
        return matching

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        cust = self._customers.get(customer_id)
        return copy.deepcopy(cust) if cust else None

    async def create_refund_payment(self, payload: ERPPaymentEntryCreate) -> Dict[str, Any]:
        new_id = f"PE-REF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        record = {
            "name": new_id,
            "payment_type": "Pay",
            "party_type": payload.party_type,
            "party": payload.party,
            "paid_amount": payload.paid_amount,
            "received_amount": payload.received_amount,
            "reference_no": payload.reference_no,
            "reference_date": payload.reference_date,
            "status": "Submitted",
            "posting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "paid_from": payload.paid_from,
            "paid_to": payload.paid_to,
            "references": [ref.model_dump() for ref in payload.references],
            "remarks": payload.remarks,
        }
        self._payments[new_id] = record
        
        # Update associated invoice if needed
        for ref in payload.references:
            inv = self._invoices.get(ref.reference_name)
            if inv:
                inv["status"] = "Partly Paid" if inv["grand_total"] > payload.paid_amount else "Cancelled"
        
        return copy.deepcopy(record)

    async def list_all_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(copy.deepcopy(self._invoices).values())[:limit]

    async def list_all_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(copy.deepcopy(self._payments).values())[:limit]


# Global singleton instance for embedded engine
_embedded_instance: Optional[EmbeddedERPNextEngine] = None


def get_erp_client() -> BaseERPNextClient:
    """
    Factory returning either the Live Frappe REST client or the Embedded ERPNext simulator
    based on the ERPNEXT_MODE configuration setting.
    """
    global _embedded_instance
    if settings.ERPNEXT_MODE.lower() == "live":
        return LiveERPNextClient()
    
    if _embedded_instance is None:
        _embedded_instance = EmbeddedERPNextEngine()
    return _embedded_instance
