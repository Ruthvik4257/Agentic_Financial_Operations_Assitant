from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from backend.app.core.database import Base


class SupportIssue(Base):
    __tablename__ = "support_issues"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(32), default="Open", nullable=False)  # Open, Closed, In Progress
    priority = Column(String(32), default="Medium", nullable=False)
    category = Column(String(64), default="Payment Dispute", nullable=False)
    opening_date = Column(String(32), nullable=False)
    resolution_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "name": self.id,
            "issue_id": self.id,
            "customer": self.customer_id,
            "customer_id": self.customer_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "issue_type": self.category,
            "opening_date": self.opening_date,
            "resolution_details": self.resolution_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
