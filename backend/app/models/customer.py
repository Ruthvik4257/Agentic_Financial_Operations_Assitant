from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime
from backend.app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    customer_name = Column(String(128), nullable=False, index=True)
    email = Column(String(128), nullable=True, index=True)
    mobile = Column(String(32), nullable=True, index=True)
    customer_group = Column(String(64), default="Retail Banking", nullable=False)
    territory = Column(String(64), default="India", nullable=False)
    credit_limit = Column(Float, default=100000.0, nullable=False)
    loyalty_tier = Column(String(32), default="Platinum", nullable=False)
    total_invoiced = Column(Float, default=0.0, nullable=False)
    lifetime_chargebacks = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "name": self.id,
            "customer_id": self.id,
            "customer_name": self.customer_name,
            "email_id": self.email,
            "email": self.email,
            "mobile_no": self.mobile,
            "mobile": self.mobile,
            "customer_group": self.customer_group,
            "territory": self.territory,
            "credit_limit": self.credit_limit,
            "loyalty_tier": self.loyalty_tier,
            "total_invoiced": self.total_invoiced,
            "lifetime_chargebacks": self.lifetime_chargebacks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
