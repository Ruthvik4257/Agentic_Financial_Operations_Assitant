from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text
from backend.app.core.database import Base


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    customer_name = Column(String(128), nullable=False)
    posting_date = Column(String(32), nullable=False)
    due_date = Column(String(32), nullable=True)
    grand_total = Column(Float, nullable=False)
    outstanding_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="Paid", nullable=False, index=True)  # Paid, Refunded, Partly Paid
    currency = Column(String(8), default="INR", nullable=False)
    item_code = Column(String(64), default="CLOUD-OPS-SEAT", nullable=False)
    item_name = Column(String(255), default="Cloud Operations Seat License", nullable=False)
    qty = Column(Float, default=1.0, nullable=False)
    rate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "name": self.id,
            "invoice_id": self.id,
            "customer": self.customer_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "posting_date": self.posting_date,
            "due_date": self.due_date,
            "grand_total": self.grand_total,
            "outstanding_amount": self.outstanding_amount,
            "status": self.status,
            "currency": self.currency,
            "items": [
                {
                    "item_code": self.item_code,
                    "item_name": self.item_name,
                    "qty": self.qty,
                    "rate": self.rate,
                    "amount": self.grand_total,
                }
            ],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
