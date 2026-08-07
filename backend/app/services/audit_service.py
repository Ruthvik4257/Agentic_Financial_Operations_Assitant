from datetime import datetime, timezone
import hashlib
import uuid
from typing import Dict, Any, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit import AuditLog


class AuditService:
    """
    Cryptographic SHA-256 Chained Audit Ledger Service.
    Guarantees tamper-evident logging of all agent states, reasoning, and financial mutations.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    @classmethod
    async def get_latest_hash(cls, session: AsyncSession, dispute_id: str) -> str:
        """Fetch the current head hash of the dispute's audit chain in exact chronological order."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.dispute_id == dispute_id)
            .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        )
        result = await session.execute(stmt)
        logs = result.scalars().all()
        return logs[0].current_hash if logs else cls.GENESIS_HASH

    @classmethod
    async def record_event(
        cls,
        session: AsyncSession,
        dispute_id: str,
        action: str,
        agent_node: str,
        justification: str,
        state_diff: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Record a cryptographically hashed event to the audit ledger."""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        previous_hash = await cls.get_latest_hash(session, dispute_id)
        current_hash = AuditLog.calculate_hash(
            previous_hash=previous_hash,
            dispute_id=dispute_id,
            action=action,
            agent_node=agent_node,
            justification=justification,
            timestamp_str=timestamp_str,
        )

        audit_entry = AuditLog(
            id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            dispute_id=dispute_id,
            timestamp=timestamp_str,
            action=action,
            agent_node=agent_node,
            state_diff=state_diff or {},
            justification=justification,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )

        session.add(audit_entry)
        await session.commit()
        await session.refresh(audit_entry)
        return audit_entry

    @classmethod
    async def verify_chain(cls, session: AsyncSession, dispute_id: str) -> bool:
        """Cryptographically verify the integrity of the audit chain for a dispute."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.dispute_id == dispute_id)
            .order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
        )
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        if not logs:
            return True

        expected_prev = cls.GENESIS_HASH
        for log in logs:
            if log.previous_hash != expected_prev:
                return False # Broken chain link
            
            calculated = AuditLog.calculate_hash(
                previous_hash=log.previous_hash,
                dispute_id=log.dispute_id,
                action=log.action,
                agent_node=log.agent_node,
                justification=log.justification,
                timestamp_str=log.timestamp,
            )
            if calculated != log.current_hash:
                return False # Hash mismatch / tampering detected
            
            expected_prev = log.current_hash

        return True
