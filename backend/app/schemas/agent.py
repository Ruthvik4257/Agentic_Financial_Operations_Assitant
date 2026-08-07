from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentDisputeInput(BaseModel):
    dispute_id: str
    customer_id: str
    invoice_id: str
    amount: float
    reason: str
    channel: str = "TELEGRAM"


class FraudAnalysisResult(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk score from 0.00 (safe) to 1.00 (fraud)")
    risk_tier: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")
    duplicate_payment_confirmed: bool = Field(default=False)
    anomaly_flags: List[str] = Field(default_factory=list)
    forensic_summary: str = Field(description="Forensic investigation explanation")
    accounting_justification: str = Field(description="ERP reconciliation ledger impact")


class PolicyEvaluationResult(BaseModel):
    action: str = Field(description="AUTO_APPROVE, REQUIRE_HITL, AUTO_REJECT")
    policy_code: str = Field(description="POL-001, POL-002, POL-003")
    reason: str
    max_allowable_refund: float


class ExecutionResult(BaseModel):
    success: bool
    payment_entry_id: Optional[str] = None
    erp_status: str
    timestamp: str
    balance_sheet_diff: Dict[str, Any] = Field(default_factory=dict)
