import copy
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal
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
            "CUST-00045": {
                "name": "CUST-00045",
                "customer_name": "Rahul Sharma",
                "customer_group": "Retail Banking",
                "territory": "India",
                "email_id": "rahul.sharma@gmail.com",
                "mobile_no": "9876543210",
                "credit_limit": 150000.00,
                "loyalty_tier": "Platinum",
                "total_invoiced": 14750.00,
                "lifetime_chargebacks": 0,
            },
            "CUST-001": {
                "name": "CUST-001",
                "customer_name": "Acme Corporation",
                "customer_group": "Enterprise Commercial",
                "territory": "United States",
                "email_id": "finance@acmecorp.com",
                "mobile_no": "9876500001",
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
                "email_id": "accounts@globexcorp.com",
                "mobile_no": "9876500002",
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
                "email_id": "billing@initechlabs.com",
                "mobile_no": "9876500003",
                "credit_limit": 10000.00,
                "loyalty_tier": "Silver",
                "total_invoiced": 8500.00,
                "lifetime_chargebacks": 0,
            },
        }

        self._issues = {}


        self._invoices = {
            "INV-2026-001": {
                "name": "INV-2026-001",
                "customer": "CUST-00045",
                "customer_name": "Rahul Sharma",
                "posting_date": "2026-08-01",
                "due_date": "2026-08-31",
                "grand_total": 2350.00,
                "outstanding_amount": 0.00,
                "status": "Paid",
                "currency": "INR",
                "items": [
                    {
                        "item_code": "CLOUD-OPS-SEAT",
                        "item_name": "Cloud Operations Seat License",
                        "qty": 1.0,
                        "rate": 2350.0,
                        "amount": 2350.0,
                    }
                ],
            },
            "INV-2026-134": {
                "name": "INV-2026-134",
                "customer": "CUST-00045",
                "customer_name": "Rahul Sharma",
                "posting_date": "2026-08-02",
                "due_date": "2026-09-01",
                "grand_total": 134.00,
                "outstanding_amount": 0.00,
                "status": "Paid",
                "currency": "USD",
                "items": [
                    {
                        "item_code": "API-MICRO-USAGE",
                        "item_name": "Cloud API Micro-Usage Billing",
                        "qty": 1.0,
                        "rate": 134.0,
                        "amount": 134.0,
                    }
                ],
            },
            "INV-2026-045": {
                "name": "INV-2026-045",
                "customer": "CUST-00045",
                "customer_name": "Rahul Sharma",
                "posting_date": "2026-08-03",
                "due_date": "2026-09-02",
                "grand_total": 8500.00,
                "outstanding_amount": 0.00,
                "status": "Paid",
                "currency": "INR",
                "items": [
                    {
                        "item_code": "ENTERPRISE-SUPPORT",
                        "item_name": "Enterprise Dedicated FinOps Support",
                        "qty": 1.0,
                        "rate": 8500.0,
                        "amount": 8500.0,
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
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            inv = await SQLLedgerService.get_invoice(session, invoice_id)
            if inv:
                return inv
        inv = self._invoices.get(invoice_id)
        return copy.deepcopy(inv) if inv else None

    async def get_or_create_invoice_for_dispute(
        self,
        invoice_id: Optional[str] = None,
        amount: Optional[float] = None,
        customer_id: str = "CUST-00045",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Locates or creates matching sales invoice and linked payment entries directly in SQL database.
        """
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.get_or_create_invoice_for_dispute(
                session=session,
                invoice_id=invoice_id,
                amount=amount,
                customer_id=customer_id,
                reason=reason,
            )

    async def list_invoices_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.get_customer_transactions(session, customer_id)

    async def get_payment_entries_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            entries = await SQLLedgerService.get_payment_entries_for_invoice(session, invoice_id)
            if entries:
                return entries
        matching = []
        for pe in self._payments.values():
            for ref in pe.get("references", []):
                if ref.get("reference_name") == invoice_id:
                    matching.append(copy.deepcopy(pe))
        return matching

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            cust = await SQLLedgerService.get_customer(session, customer_id)
            if cust:
                return cust
        cust = self._customers.get(customer_id)
        return copy.deepcopy(cust) if cust else None

    async def create_refund_payment(self, payload: ERPPaymentEntryCreate) -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.create_refund_payment(session, payload)

    async def list_all_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.list_all_invoices(session, limit)

    async def list_all_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.list_all_payments(session, limit)

    async def find_customer_by_identifier(self, identifier_type: str, identifier_value: str) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.find_customer_by_identifier(session, identifier_type, identifier_value)

    async def create_support_issue(self, customer_id: str, subject: str, description: str, priority: str = "Medium", category: str = "Payment Dispute") -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            return await SQLLedgerService.create_support_issue(session, customer_id, subject, description, priority, category)

    async def get_customer_transactions(self, customer_id: str) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            from backend.app.services.sql_ledger_service import SQLLedgerService
            txs = await SQLLedgerService.get_customer_transactions(session, customer_id)
            if txs:
                return txs
        invoices = [copy.deepcopy(inv) for inv in self._invoices.values() if inv.get("customer") == customer_id]
        return invoices


# Global singleton instance for embedded engine
_embedded_instance: Optional[EmbeddedERPNextEngine] = None


def get_erp_client() -> BaseERPNextClient:
    """
    Factory returning the native SQL Ledger database client.
    """
    global _embedded_instance
    if _embedded_instance is None:
        _embedded_instance = EmbeddedERPNextEngine()
    return _embedded_instance

