from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.core.config import settings

router = APIRouter(prefix="/policies", tags=["Financial Policies"])


class PolicyConfigModel(BaseModel):
    max_auto_refund_limit: float = Field(default=200.00, ge=10.0, le=5000.0)
    max_fraud_risk_threshold: float = Field(default=0.30, ge=0.05, le=0.95)
    max_daily_refund_cap: float = Field(default=5000.00, ge=100.0)
    require_2fa_above: float = Field(default=1000.00, ge=200.0)
    auto_block_suspicious_accounts: bool = Field(default=True)


# In-memory policy state initialized with environment defaults
_current_policy = PolicyConfigModel(
    max_auto_refund_limit=settings.MAX_AUTO_REFUND_LIMIT,
    max_fraud_risk_threshold=settings.MAX_FRAUD_RISK_THRESHOLD,
    max_daily_refund_cap=settings.MAX_DAILY_REFUND_CAP,
    require_2fa_above=1000.00,
    auto_block_suspicious_accounts=True,
)


@router.get("", response_model=PolicyConfigModel)
async def get_active_policies():
    """Returns the current financial governance thresholds."""
    return _current_policy


@router.put("", response_model=PolicyConfigModel)
async def update_policies(new_policy: PolicyConfigModel):
    """Updates financial governance thresholds in real-time."""
    global _current_policy
    _current_policy = new_policy
    settings.MAX_AUTO_REFUND_LIMIT = new_policy.max_auto_refund_limit
    settings.MAX_FRAUD_RISK_THRESHOLD = new_policy.max_fraud_risk_threshold
    settings.MAX_DAILY_REFUND_CAP = new_policy.max_daily_refund_cap
    return _current_policy
