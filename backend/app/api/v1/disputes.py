import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.models.audit import AuditLog
from backend.app.models.approval import ApprovalRequest
from backend.app.schemas.dispute import DisputeResponse, DisputeDossierResponse, DisputeCreateRequest
from backend.app.services.erpnext_mock import get_erp_client
from backend.app.api.v1.websocket import ws_manager
from agents.graph import finops_agent

router = APIRouter(prefix="/disputes", tags=["Disputes"])


@router.get("", response_model=List[DisputeResponse])
async def list_disputes(
    status: Optional[str] = None,
    risk_tier: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Dispute).order_by(Dispute.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Dispute.status == status)
    if risk_tier:
        stmt = stmt.where(Dispute.risk_tier == risk_tier)
    
    result = await db.execute(stmt)
    disputes = result.scalars().all()
    return [d.to_dict() for d in disputes]


@router.post("/simulate")
async def simulate_dispute(
    payload: DisputeCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Simulates a dispute intake from Telegram/Web to test autonomous agent workflows.
    """
    dispute_id = f"DISP-{payload.invoice_id}-{uuid.uuid4().hex[:6].upper()}"
    
    dispute = Dispute(
        id=dispute_id,
        customer_id=payload.customer_id,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        currency=payload.currency,
        reason=payload.reason,
        status=DisputeStatus.PENDING_INVESTIGATION,
    )
    db.add(dispute)
    await db.commit()

    # Broadcast WebSocket Event
    await ws_manager.broadcast({
        "type": "DISPUTE_INGESTED",
        "dispute_id": dispute_id,
        "invoice_id": payload.invoice_id,
        "amount": payload.amount,
        "channel": "SIMULATION_DECK",
    })

    # Run LangGraph State Machine
    inputs = {
        "messages": [{"role": "user", "content": payload.reason}],
        "dispute": dispute,
    }
    agent_result = await finops_agent.ainvoke(inputs)

    fraud = agent_result.get("fraud")
    verdict = agent_result.get("policy_verdict")
    exec_res = agent_result.get("execution_result")

    if fraud:
        dispute.fraud_score = fraud.risk_score
        dispute.risk_tier = RiskTier(fraud.risk_tier) if fraud.risk_tier in RiskTier.__members__ else RiskTier.LOW
        dispute.is_duplicate_payment = fraud.duplicate_payment_confirmed
        dispute.forensic_summary = fraud.forensic_summary

    if verdict == "AUTO_APPROVE" and exec_res:
        dispute.status = DisputeStatus.EXECUTED
        dispute.erp_payment_entry_id = exec_res.get("payment_entry_id")
        await db.commit()

        await ws_manager.broadcast({
            "type": "REFUND_AUTO_EXECUTED",
            "dispute_id": dispute_id,
            "payment_entry": exec_res.get("payment_entry_id"),
            "amount": payload.amount,
            "risk_score": fraud.risk_score if fraud else 0.08,
        })
    elif verdict == "REQUIRE_HITL":
        dispute.status = DisputeStatus.AWAITING_APPROVAL
        await db.commit()

        await ws_manager.broadcast({
            "type": "HITL_ESCALATION_TRIGGERED",
            "dispute_id": dispute_id,
            "amount": payload.amount,
            "risk_score": fraud.risk_score if fraud else 0.45,
        })
    else:
        dispute.status = DisputeStatus.REJECTED
        await db.commit()

    return dispute.to_dict()


@router.get("/{dispute_id}", response_model=DisputeDossierResponse)
async def get_dispute_dossier(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(stmt)
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")

    erp_client = get_erp_client()
    erp_invoice = await erp_client.get_invoice(dispute.invoice_id)
    erp_payments = await erp_client.get_payment_entries_for_invoice(dispute.invoice_id)

    stmt_audit = select(AuditLog).where(AuditLog.dispute_id == dispute_id).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
    audit_res = await db.execute(stmt_audit)
    audit_logs = [log.to_dict() for log in audit_res.scalars().all()]

    stmt_app = select(ApprovalRequest).where(ApprovalRequest.dispute_id == dispute_id)
    app_res = await db.execute(stmt_app)
    approval = app_res.scalar_one_or_none()

    return {
        "dispute": dispute.to_dict(),
        "erp_invoice": erp_invoice,
        "erp_payments": erp_payments,
        "audit_trail": audit_logs,
        "approval_request": approval.to_dict() if approval else None,
    }
