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

    async def get_or_create_invoice_for_dispute(
        self,
        invoice_id: Optional[str] = None,
        amount: Optional[float] = None,
        customer_id: str = "CUST-001",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Dynamically locates matching customer invoice or generates a valid ERPNext Sales Invoice
        and associated payment captures for any disputed amount (e.g. $200.00).
        """
        # If specific invoice exists, return it
        if invoice_id and invoice_id in self._invoices:
            inv = self._invoices[invoice_id]
            if amount and amount != inv["grand_total"]:
                # If custom amount reported on invoice, adapt invoice grand total
                inv["grand_total"] = amount
            return copy.deepcopy(inv)

        # Generate standard identifier if missing
        inv_id = invoice_id or (f"INV-2026-{int(amount)}" if amount else "INV-2026-001")
        dispute_amt = amount if amount and amount > 0 else 200.00

        # Create new Sales Invoice record in ERPNext memory ledger
        cust = self._customers.get(customer_id, self._customers["CUST-001"])
        new_inv = {
            "name": inv_id,
            "customer": customer_id,
            "customer_name": cust.get("customer_name", "Acme Corporation"),
            "posting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "due_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "grand_total": dispute_amt,
            "outstanding_amount": 0.00,
            "status": "Paid",
            "currency": "USD",
            "items": [
                {
                    "item_code": "CLOUD-FIN-OPS",
                    "item_name": f"Financial Operations Subscription / Disputed Charge ({reason or 'Standard Service'})",
                    "qty": 1.0,
                    "rate": dispute_amt,
                    "amount": dispute_amt,
                }
            ],
        }
        self._invoices[inv_id] = new_inv

        # Register linked payment entry
        pe_id = f"PE-{inv_id.replace('INV-', '')}A"
        if pe_id not in self._payments:
            self._payments[pe_id] = {
                "name": pe_id,
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": customer_id,
                "paid_amount": dispute_amt,
                "received_amount": dispute_amt,
                "reference_no": f"TX-PAY-{inv_id}",
                "reference_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "status": "Submitted",
                "posting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "references": [{"reference_doctype": "Sales Invoice", "reference_name": inv_id, "allocated_amount": dispute_amt}],
                "remarks": f"Credit Card Settle - Gateway Capture ({dispute_amt:.2f} USD)",
            }

        # If duplicate charge is reported, also register duplicate payment entry
        if any(w in (reason or "").lower() for w in ["double", "duplicate", "twice", "two times"]):
            pe_dup_id = f"PE-{inv_id.replace('INV-', '')}B-DUP"
            if pe_dup_id not in self._payments:
                self._payments[pe_dup_id] = {
                    "name": pe_dup_id,
                    "payment_type": "Receive",
                    "party_type": "Customer",
                    "party": customer_id,
                    "paid_amount": dispute_amt,
                    "received_amount": dispute_amt,
                    "reference_no": f"TX-PAY-{inv_id}-DUP",
                    "reference_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "status": "Submitted",
                    "posting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "references": [{"reference_doctype": "Sales Invoice", "reference_name": inv_id, "allocated_amount": dispute_amt}],
                    "remarks": f"Duplicate gateway capture anomaly ({dispute_amt:.2f} USD)",
                }

        return copy.deepcopy(new_inv)

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
        
        # Update associated invoice in ERPNext ledger
        for ref in payload.references:
            inv = self._invoices.get(ref.reference_name)
            if inv:
                inv["status"] = "Partly Paid" if inv["grand_total"] > payload.paid_amount else "Refunded"
                inv["outstanding_amount"] = 0.00
        
        # Update customer ledger totals
        cust = self._customers.get(payload.party)
        if cust:
            cust["total_invoiced"] = max(0.0, cust.get("total_invoiced", 0.0) - payload.paid_amount)
        
        return copy.deepcopy(record)

    async def list_all_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(copy.deepcopy(self._invoices).values())[:limit]

    async def list_all_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(copy.deepcopy(self._payments).values())[:limit]

    async def find_customer_by_identifier(self, identifier_type: str, identifier_value: str) -> List[Dict[str, Any]]:
        val_clean = str(identifier_value).strip().lower().replace(" ", "").replace("-", "")
        matches = []

        for cust in self._customers.values():
            c_id = cust.get("name", "").lower().replace(" ", "").replace("-", "")
            c_email = cust.get("email_id", "").lower().strip()
            c_mobile = cust.get("mobile_no", "").lower().replace(" ", "").replace("-", "")
            c_name = cust.get("customer_name", "").lower()

            if identifier_type == "mobile":
                if val_clean in c_mobile or c_mobile.endswith(val_clean) or val_clean.endswith(c_mobile):
                    matches.append(copy.deepcopy(cust))
            elif identifier_type == "email":
                if val_clean in c_email:
                    matches.append(copy.deepcopy(cust))
            elif identifier_type == "customer_id":
                if val_clean == c_id or val_clean in c_id:
                    matches.append(copy.deepcopy(cust))
            else:
                if val_clean in c_id or val_clean in c_email or val_clean in c_mobile or val_clean in c_name:
                    matches.append(copy.deepcopy(cust))

        return matches

    async def create_support_issue(self, customer_id: str, subject: str, description: str, priority: str = "Medium", category: str = "Payment Dispute") -> Dict[str, Any]:
        issue_id = f"ISSUE-2026-{datetime.now(timezone.utc).strftime('%H%M%S')}"
        record = {
            "name": issue_id,
            "customer": customer_id,
            "subject": subject,
            "description": description,
            "status": "Open",
            "priority": priority,
            "issue_type": category,
            "opening_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "resolution_details": None,
        }
        self._issues[issue_id] = record
        return copy.deepcopy(record)

    async def get_customer_transactions(self, customer_id: str) -> List[Dict[str, Any]]:
        invoices = [copy.deepcopy(inv) for inv in self._invoices.values() if inv.get("customer") == customer_id]
        if not invoices:
            # Provide sample invoice if empty
            invoices = [
                {
                    "name": "INV-2026-001",
                    "customer": customer_id,
                    "customer_name": self._customers.get(customer_id, {}).get("customer_name", "Rahul Sharma"),
                    "posting_date": "2026-08-01",
                    "grand_total": 2350.00,
                    "status": "Paid",
                    "currency": "INR",
                    "items": [{"item_name": "Digital Banking Merchant Payment / Seat License", "rate": 2350.00}],
                }
            ]
        return invoices



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
