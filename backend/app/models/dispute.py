import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Enum as SQLEnum,
    Text,
    JSON,
    Boolean,
)
from backend.app.core.database import Base


class DisputeStatus(str, enum.Enum):
    PENDING_INVESTIGATION = "PENDING_INVESTIGATION"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class RiskTier(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    invoice_id = Column(String(64), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    reason = Column(Text, nullable=False)
    
    # Financial investigation & fraud metrics
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.PENDING_INVESTIGATION, nullable=False, index=True)
    fraud_score = Column(Float, default=0.0, nullable=False)
    risk_tier = Column(SQLEnum(RiskTier), default=RiskTier.LOW, nullable=False)
    is_duplicate_payment = Column(Boolean, default=False, nullable=False)
    
    # Forensic reasoning & evidence
    forensic_summary = Column(Text, nullable=True)
    gemini_reasoning = Column(Text, nullable=True)
    raw_evidence = Column(JSON, nullable=True)
    
    # ERPNext Execution Reference
    erp_payment_entry_id = Column(String(64), nullable=True)
    erp_refund_status = Column(String(32), nullable=True)
    telegram_chat_id = Column(String(64), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "status": self.status.value if isinstance(self.status, DisputeStatus) else self.status,
            "fraud_score": self.fraud_score,
            "risk_tier": self.risk_tier.value if isinstance(self.risk_tier, RiskTier) else self.risk_tier,
            "is_duplicate_payment": self.is_duplicate_payment,
            "forensic_summary": self.forensic_summary,
            "gemini_reasoning": self.gemini_reasoning,
            "erp_payment_entry_id": self.erp_payment_entry_id,
            "erp_refund_status": self.erp_refund_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
