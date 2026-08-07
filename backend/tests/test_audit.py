import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.database import Base
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.services.audit_service import AuditService


@pytest.mark.asyncio
async def test_cryptographic_audit_chain():
    # Setup in-memory test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        # Create base dispute
        dispute = Dispute(
            id="DISP-TEST-99",
            customer_id="CUST-001",
            invoice_id="INV-2026-001",
            amount=150.00,
            currency="USD",
            reason="Test duplicate billing",
            status=DisputeStatus.PENDING_INVESTIGATION,
            fraud_score=0.10,
            risk_tier=RiskTier.LOW,
        )
        session.add(dispute)
        await session.commit()

        # Step 1: Record INTAKE event
        log1 = await AuditService.record_event(
            session=session,
            dispute_id="DISP-TEST-99",
            action="INTAKE",
            agent_node="SupervisorNode",
            justification="Ingested customer dispute from Telegram",
            state_diff={"invoice_id": "INV-2026-001", "amount": 150.0},
        )
        assert log1.previous_hash == AuditService.GENESIS_HASH

        # Step 2: Record FRAUD_EVALUATED event
        log2 = await AuditService.record_event(
            session=session,
            dispute_id="DISP-TEST-99",
            action="FRAUD_EVALUATED",
            agent_node="FraudAnalystNode",
            justification="Gemini 2.0 scored risk at 0.08 (low)",
            state_diff={"risk_score": 0.08, "duplicate_confirmed": True},
        )
        assert log2.previous_hash == log1.current_hash

        # Step 3: Record REFUND_EXECUTED event
        log3 = await AuditService.record_event(
            session=session,
            dispute_id="DISP-TEST-99",
            action="REFUND_EXECUTED",
            agent_node="RefundExecutorNode",
            justification="Posted Payment Entry PE-REF-001 to ERPNext",
            state_diff={"payment_entry": "PE-REF-001"},
        )
        assert log3.previous_hash == log2.current_hash

        # Step 4: Verify complete cryptographic chain integrity
        is_valid = await AuditService.verify_chain(session, "DISP-TEST-99")
        assert is_valid is True
