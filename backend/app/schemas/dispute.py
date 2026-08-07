from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.dispute import DisputeStatus, RiskTier


class DisputeCreateRequest(BaseModel):
    customer_id: str = Field(..., example="CUST-001")
    invoice_id: str = Field(..., example="INV-2026-001")
    amount: float = Field(..., gt=0.0, example=150.0)
    reason: str = Field(..., example="Double charged for invoice on credit card")
    currency: str = Field(default="USD", example="USD")


class DisputeResponse(BaseModel):
    id: str
    customer_id: str
    invoice_id: str
    amount: float
    currency: str
    reason: str
    status: str
    fraud_score: float
    risk_tier: str
    is_duplicate_payment: bool
    forensic_summary: Optional[str] = None
    gemini_reasoning: Optional[str] = None
    erp_payment_entry_id: Optional[str] = None
    erp_refund_status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    resolved_at: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalActionRequest(BaseModel):
    manager_id: str = Field(default="MGR-001")
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    manager_notes: Optional[str] = Field(default="Manager manual review signoff")
    channel: str = Field(default="DASHBOARD")


class DisputeDossierResponse(BaseModel):
    dispute: DisputeResponse
    erp_invoice: Optional[Dict[str, Any]] = None
    erp_payments: Optional[List[Dict[str, Any]]] = None
    audit_trail: List[Dict[str, Any]] = []
    approval_request: Optional[Dict[str, Any]] = None
