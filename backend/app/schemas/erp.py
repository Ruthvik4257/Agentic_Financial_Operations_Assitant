from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ERPInvoiceItem(BaseModel):
    item_code: str
    item_name: str
    qty: float
    rate: float
    amount: float


class ERPSalesInvoice(BaseModel):
    name: str # e.g. "INV-2026-001"
    customer: str # e.g. "CUST-001"
    customer_name: Optional[str] = None
    posting_date: str
    grand_total: float
    outstanding_amount: float
    status: str # "Paid", "Unpaid", "Overdue", "Partly Paid", "Cancelled"
    currency: str = "USD"
    items: List[ERPInvoiceItem] = []
    payments: List[Dict[str, Any]] = []


class ERPPaymentEntryReference(BaseModel):
    reference_doctype: str = "Sales Invoice"
    reference_name: str
    allocated_amount: float


class ERPPaymentEntryCreate(BaseModel):
    payment_type: str = "Pay" # "Pay" for refund, "Receive" for customer payment
    party_type: str = "Customer"
    party: str
    paid_amount: float
    received_amount: float
    reference_no: str
    reference_date: str
    paid_from: str = "1110 - Bank Account - TC"
    paid_to: str = "2110 - Debtors - TC"
    references: List[ERPPaymentEntryReference]
    remarks: str


class ERPPaymentEntry(BaseModel):
    name: str # e.g. "PE-2026-001"
    payment_type: str
    party_type: str
    party: str
    paid_amount: float
    received_amount: float
    reference_no: Optional[str] = None
    status: str = "Submitted"
    posting_date: str
    remarks: Optional[str] = None


class ERPCustomer(BaseModel):
    name: str
    customer_name: str
    customer_group: str = "Commercial"
    territory: str = "United States"
    credit_limit: float = 10000.00
    loyalty_tier: str = "Gold"
    total_invoiced: float = 0.0
    lifetime_chargebacks: int = 0
