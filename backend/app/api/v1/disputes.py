from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.models.audit import AuditLog
from backend.app.models.approval import ApprovalRequest
from backend.app.schemas.dispute import DisputeResponse, DisputeDossierResponse
from backend.app.services.erpnext_mock import get_erp_client

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


@router.get("/{dispute_id}", response_model=DisputeDossierResponse)
async def get_dispute_dossier(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch Dispute record
    stmt = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(stmt)
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")

    # 2. Fetch ERPNext live data
    erp_client = get_erp_client()
    erp_invoice = await erp_client.get_invoice(dispute.invoice_id)
    erp_payments = await erp_client.get_payment_entries_for_invoice(dispute.invoice_id)

    # 3. Fetch Audit Trail
    stmt_audit = select(AuditLog).where(AuditLog.dispute_id == dispute_id).order_by(AuditLog.timestamp.asc())
    audit_res = await db.execute(stmt_audit)
    audit_logs = [log.to_dict() for log in audit_res.scalars().all()]

    # 4. Fetch Approval Request if exists
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
