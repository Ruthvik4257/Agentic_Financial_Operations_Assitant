from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.dispute import Dispute, DisputeStatus
from backend.app.models.approval import ApprovalRequest
from backend.app.schemas.dispute import ApprovalActionRequest
from backend.app.services.audit_service import AuditService
from backend.app.services.erpnext_mock import get_erp_client
from backend.app.schemas.erp import ERPPaymentEntryCreate, ERPPaymentEntryReference

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.post("/{dispute_id}")
async def process_approval_decision(
    dispute_id: str,
    action: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch Dispute
    stmt = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(stmt)
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    # 2. Update Approval record
    stmt_app = select(ApprovalRequest).where(ApprovalRequest.dispute_id == dispute_id)
    app_res = await db.execute(stmt_app)
    approval = app_res.scalar_one_or_none()
    
    if not approval:
        approval = ApprovalRequest(
            id=f"APP-{dispute_id}",
            dispute_id=dispute_id,
            manager_id=action.manager_id,
            channel=action.channel,
            amount=dispute.amount,
            risk_score=dispute.fraud_score,
            escalation_reason="Human-in-the-Loop financial governance review",
        )
        db.add(approval)

    approval.decision = action.decision
    approval.manager_notes = action.manager_notes
    approval.decided_at = datetime.now(timezone.utc)

    # 3. If Approved, execute ERPNext refund payment entry
    if action.decision == "APPROVED":
        erp_client = get_erp_client()
        invoice = await erp_client.get_invoice(dispute.invoice_id)
        invoice_total = invoice.get("grand_total", dispute.amount) if invoice else dispute.amount
        safe_amount = min(dispute.amount, invoice_total)

        refund_payload = ERPPaymentEntryCreate(
            payment_type="Pay",
            party_type="Customer",
            party=dispute.customer_id,
            paid_amount=safe_amount,
            received_amount=safe_amount,
            reference_no=f"HITL-{dispute_id}",
            reference_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            paid_from="1110 - Bank Account - TC",
            paid_to="2110 - Debtors - TC",
            references=[
                ERPPaymentEntryReference(
                    reference_doctype="Sales Invoice",
                    reference_name=dispute.invoice_id,
                    allocated_amount=safe_amount,
                )
            ],
            remarks=f"Manager Approved Refund ({action.manager_id}): {action.manager_notes}",
        )
        erp_res = await erp_client.create_refund_payment(refund_payload)
        
        dispute.status = DisputeStatus.EXECUTED
        dispute.erp_payment_entry_id = erp_res.get("name")
        dispute.resolved_at = datetime.now(timezone.utc)

        # Record Audit Event
        await AuditService.record_event(
            session=db,
            dispute_id=dispute_id,
            action="MANAGER_APPROVED_AND_EXECUTED",
            agent_node="HumanManagerGate",
            justification=f"Approved by {action.manager_id} via {action.channel}. ERPNext {erp_res.get('name')} created.",
            state_diff={"manager_id": action.manager_id, "payment_entry": erp_res.get("name")},
        )
    else:
        dispute.status = DisputeStatus.REJECTED
        dispute.resolved_at = datetime.now(timezone.utc)

        await AuditService.record_event(
            session=db,
            dispute_id=dispute_id,
            action="MANAGER_REJECTED",
            agent_node="HumanManagerGate",
            justification=f"Rejected by {action.manager_id} via {action.channel}: {action.manager_notes}",
            state_diff={"manager_id": action.manager_id, "rejection_notes": action.manager_notes},
        )

    await db.commit()
    await db.refresh(dispute)

    # 4. Proactively notify customer on Telegram in real time
    try:
        from backend.app.services.telegram_service import notify_customer_refund_status
        import asyncio
        asyncio.create_task(
            notify_customer_refund_status(
                customer_id=dispute.customer_id,
                dispute_id=dispute.id,
                invoice_id=dispute.invoice_id,
                amount=dispute.amount,
                status=dispute.status.value,
                payment_entry_id=dispute.erp_payment_entry_id,
                currency=dispute.currency,
                manager_notes=action.manager_notes,
                chat_id=dispute.telegram_chat_id,
            )
        )
    except Exception:
        pass

    return {"success": True, "status": dispute.status.value, "erp_payment_entry": dispute.erp_payment_entry_id}

