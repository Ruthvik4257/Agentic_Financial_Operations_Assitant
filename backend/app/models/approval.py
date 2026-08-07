from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    ForeignKey,
    Float,
)
from backend.app.core.database import Base


class ApprovalRequest(Base):
    __tablename__ = "approvals"

    id = Column(String(64), primary_key=True, index=True)
    dispute_id = Column(String(64), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_id = Column(String(64), nullable=True)
    channel = Column(String(32), default="TELEGRAM", nullable=False) # TELEGRAM or DASHBOARD
    
    amount = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    escalation_reason = Column(Text, nullable=False)
    
    decision = Column(String(32), default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED
    manager_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "dispute_id": self.dispute_id,
            "manager_id": self.manager_id,
            "channel": self.channel,
            "amount": self.amount,
            "risk_score": self.risk_score,
            "escalation_reason": self.escalation_reason,
            "decision": self.decision,
            "manager_notes": self.manager_notes,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
