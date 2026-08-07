from datetime import datetime, timezone
import hashlib
from sqlalchemy import (
    Column,
    String,
    Text,
    JSON,
    ForeignKey,
)
from backend.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    dispute_id = Column(String(64), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(String(64), nullable=False, index=True) # Standardized ISO-8601 string for cross-DB determinism
    
    action = Column(String(64), nullable=False) # e.g. INTAKE, FRAUD_EVALUATED, POLICY_TRIGGERED, HITL_PAUSED, MANAGER_APPROVED, ERP_EXECUTED
    agent_node = Column(String(64), nullable=False) # e.g. SupervisorNode, FraudAnalystNode, PolicyGatekeeper, RefundExecutor
    
    state_diff = Column(JSON, nullable=True)
    justification = Column(Text, nullable=False)
    
    # Cryptographic SHA-256 Chained Hashes
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, unique=True)

    @staticmethod
    def calculate_hash(previous_hash: str, dispute_id: str, action: str, agent_node: str, justification: str, timestamp_str: str) -> str:
        payload = f"{previous_hash}|{dispute_id}|{action}|{agent_node}|{justification}|{timestamp_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self):
        return {
            "id": self.id,
            "dispute_id": self.dispute_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "agent_node": self.agent_node,
            "state_diff": self.state_diff,
            "justification": self.justification,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
        }
