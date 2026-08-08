import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.api.v1.websocket import ws_manager
from agents.graph import finops_agent

router = APIRouter(prefix="/gateways", tags=["Payment Gateways"])


class StripeDisputeWebhookPayload(BaseModel):
    id: str = Field(..., example="dp_1Mqq152eZvKYlo2C0V8...")
    object: str = "dispute"
    amount: float = Field(..., example=150.0)
    currency: str = "usd"
    charge: str = Field(..., example="ch_1Mqq142eZvKYlo2C...")
    invoice_id: str = Field(default="INV-2026-001", example="INV-2026-001")
    reason: str = Field(default="duplicate", example="duplicate")
    status: str = "needs_response"


@router.post("/stripe/webhook")
async def ingest_stripe_dispute(
    payload: StripeDisputeWebhookPayload,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingests inbound automated dispute webhooks from Stripe or Payment Processors,
    cross-referencing ERPNext without human intervention.
    """
    dispute_id = f"DISP-STRIPE-{payload.invoice_id}-{uuid.uuid4().hex[:6].upper()}"

    dispute = Dispute(
        id=dispute_id,
        customer_id="CUST-001",
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        reason=f"Stripe Chargeback Webhook ({payload.reason}) on Charge {payload.charge}",
        status=DisputeStatus.PENDING_INVESTIGATION,
    )
    db.add(dispute)
    await db.commit()

    # Broadcast event to React Hub via WebSockets
    await ws_manager.broadcast({
        "type": "GATEWAY_DISPUTE_INGESTED",
        "gateway": "STRIPE",
        "dispute_id": dispute_id,
        "invoice_id": payload.invoice_id,
        "amount": payload.amount,
    })

    # Execute LangGraph Pipeline
    inputs = {
        "messages": [{"role": "user", "content": dispute.reason}],
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
            "type": "GATEWAY_REFUND_AUTO_EXECUTED",
            "dispute_id": dispute_id,
            "payment_entry": exec_res.get("payment_entry_id"),
            "amount": payload.amount,
        })

        try:
            from backend.app.services.telegram_service import notify_customer_refund_status
            import asyncio
            asyncio.create_task(
                notify_customer_refund_status(
                    customer_id=dispute.customer_id,
                    dispute_id=dispute.id,
                    invoice_id=dispute.invoice_id,
                    amount=dispute.amount,
                    status="EXECUTED",
                    payment_entry_id=exec_res.get("payment_entry_id"),
                    currency=dispute.currency,
                )
            )
        except Exception:
            pass
    elif verdict == "REQUIRE_HITL":
        dispute.status = DisputeStatus.AWAITING_APPROVAL
        await db.commit()

        await ws_manager.broadcast({
            "type": "GATEWAY_HITL_ESCALATED",
            "dispute_id": dispute_id,
            "amount": payload.amount,
        })
    else:
        dispute.status = DisputeStatus.REJECTED
        await db.commit()

    return {
        "received": True,
        "dispute_id": dispute_id,
        "status": dispute.status.value,
        "fraud_score": dispute.fraud_score,
        "erp_payment_entry": dispute.erp_payment_entry_id,
    }
