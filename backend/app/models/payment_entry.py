from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from backend.app.core.database import Base


class PaymentEntry(Base):
    __tablename__ = "payment_entries"

    id = Column(String(64), primary_key=True, index=True)
    payment_type = Column(String(32), nullable=False)  # Receive, Pay
    party_type = Column(String(32), default="Customer", nullable=False)
    party_id = Column(String(64), nullable=False, index=True)
    invoice_id = Column(String(64), nullable=True, index=True)
    paid_amount = Column(Float, nullable=False)
    received_amount = Column(Float, nullable=False)
    status = Column(String(32), default="Submitted", nullable=False)
    reference_no = Column(String(128), nullable=True, index=True)
    reference_date = Column(String(32), nullable=True)
    posting_date = Column(String(32), nullable=False)
    paid_from = Column(String(128), default="1110 - Bank Account - TC", nullable=True)
    paid_to = Column(String(128), default="2110 - Debtors - TC", nullable=True)
    remarks = Column(Text, nullable=True)
    references = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "name": self.id,
            "payment_id": self.id,
            "payment_type": self.payment_type,
            "party_type": self.party_type,
            "party": self.party_id,
            "party_id": self.party_id,
            "invoice_id": self.invoice_id,
            "paid_amount": self.paid_amount,
            "received_amount": self.received_amount,
            "status": self.status,
            "reference_no": self.reference_no,
            "reference_date": self.reference_date,
            "posting_date": self.posting_date,
            "paid_from": self.paid_from,
            "paid_to": self.paid_to,
            "remarks": self.remarks,
            "references": self.references or [{"reference_doctype": "Sales Invoice", "reference_name": self.invoice_id, "allocated_amount": self.paid_amount}],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
