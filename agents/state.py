from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DisputeRecord(BaseModel):
    dispute_id: str
    customer_id: str
    invoice_id: str
    amount: float
    currency: str = "USD"
    reason: str
    status: str = "PENDING_INVESTIGATION" # PENDING_INVESTIGATION, AWAITING_APPROVAL, APPROVED, REJECTED, EXECUTED


class FraudAssessment(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_tier: str = "LOW" # LOW, MEDIUM, HIGH, CRITICAL
    duplicate_payment_confirmed: bool = False
    anomaly_flags: List[str] = []
    forensic_summary: str = ""
    accounting_justification: str = ""


class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    dispute: DisputeRecord
    erp_invoice: Optional[Dict[str, Any]]
    erp_payments: Optional[List[Dict[str, Any]]]
    customer_profile: Optional[Dict[str, Any]]
    fraud: Optional[FraudAssessment]
    policy_verdict: Optional[str] # AUTO_APPROVE, REQUIRE_HITL, AUTO_REJECT
    policy_reason: Optional[str]
    manager_decision: Optional[str] # APPROVED, REJECTED
    manager_notes: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    audit_hash: Optional[str]
    current_node: str
    error: Optional[str]
