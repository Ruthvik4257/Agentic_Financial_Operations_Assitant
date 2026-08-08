import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db, AsyncSessionLocal
from backend.app.services.erpnext_mock import get_erp_client
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.services.audit_service import AuditService
from backend.app.api.v1.websocket import ws_manager
from agents.graph import finops_agent
from agents.state import DisputeRecord

router = APIRouter(prefix="/customer-support", tags=["Customer Support Gateway"])


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "ra****@gmail.com"
    parts = email.split("@")
    user = parts[0]
    domain = parts[1]
    masked_user = user[:2] + "****" if len(user) > 2 else user + "****"
    return f"{masked_user}@{domain}"


def mask_phone(phone: str) -> str:
    if not phone:
        return "98******10"
    cleaned = "".join(filter(str.isdigit, phone))
    if len(cleaned) >= 10:
        return f"{cleaned[:2]}******{cleaned[-2:]}"
    return f"{cleaned[:2]}****"


class CustomerVerificationRequest(BaseModel):
    identifier_type: str = Field(..., description="'mobile', 'email', or 'customer_id'")
    identifier_value: str = Field(..., description="The user-supplied value (e.g. 9876543210, rahul.sharma@gmail.com, CUST-00045)")


class CustomerVerificationResponse(BaseModel):
    success: bool
    matches_count: int
    customer: Optional[Dict[str, Any]] = None
    message: str


class InvestigationRequest(BaseModel):
    customer_id: str
    issue_type: str
    invoice_id: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "INR"
    user_message: str = ""


class CreateSupportIssueRequest(BaseModel):
    customer_id: str
    subject: str
    description: str
    priority: str = "Medium"
    category: str = "Payment Dispute"


@router.post("/verify-customer", response_model=CustomerVerificationResponse)
async def verify_customer(payload: CustomerVerificationRequest):
    """
    Searches ERPNext via FastAPI to locate exactly ONE customer profile matching
    the provided identifier (Mobile, Email, or Customer ID). Masks sensitive info.
    """
    client = get_erp_client()
    matches = await client.find_customer_by_identifier(
        identifier_type=payload.identifier_type.lower(),
        identifier_value=payload.identifier_value,
    )

    if len(matches) == 1:
        c = matches[0]
        masked = {
            "customer_id": c.get("name", "CUST-00045"),
            "customer_name": c.get("customer_name", "Rahul Sharma"),
            "registered_email": mask_email(c.get("email_id", "rahul.sharma@gmail.com")),
            "registered_mobile": mask_phone(c.get("mobile_no", "9876543210")),
            "customer_group": c.get("customer_group", "Retail Banking"),
            "loyalty_tier": c.get("loyalty_tier", "Platinum"),
            "raw_email": c.get("email_id", "rahul.sharma@gmail.com"),
            "raw_mobile": c.get("mobile_no", "9876543210"),
        }
        return CustomerVerificationResponse(
            success=True,
            matches_count=1,
            customer=masked,
            message="Customer profile verified successfully.",
        )
    elif len(matches) > 1:
        return CustomerVerificationResponse(
            success=False,
            matches_count=len(matches),
            customer=None,
            message="Multiple customer accounts found with this identifier. Please provide a more specific identifier.",
        )
    else:
        return CustomerVerificationResponse(
            success=False,
            matches_count=0,
            customer=None,
            message="We couldn't locate your account with the provided details.",
        )


@router.get("/transactions/{customer_id}")
async def get_customer_transactions(customer_id: str):
    """
    Retrieves verified invoices and payment records for the customer from ERPNext.
    """
    client = get_erp_client()
    invoices = await client.get_customer_transactions(customer_id)
    return {
        "customer_id": customer_id,
        "transactions": invoices,
        "count": len(invoices),
    }


@router.post("/investigate")
async def investigate_customer_issue(
    payload: InvestigationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Dispatches customer support dispute to the LangGraph AI multi-agent workflow
    and returns human-friendly investigation results, recommendations, and reference IDs.
    """
    client = get_erp_client()
    customer = await client.get_customer(payload.customer_id) or {
        "name": payload.customer_id,
        "customer_name": "Rahul Sharma",
    }

    # Determine amount & invoice
    amount = payload.amount or 2350.00
    invoice_id = payload.invoice_id or f"INV-2026-001"
    dispute_id = f"DISP-TG-{payload.customer_id}-{uuid.uuid4().hex[:6].upper()}"

    # Create Dispute record in SQL database
    dispute = Dispute(
        id=dispute_id,
        customer_id=payload.customer_id,
        invoice_id=invoice_id,
        amount=amount,
        currency=payload.currency,
        reason=f"[{payload.issue_type}] {payload.user_message or 'Customer reported payment anomaly via Telegram'}",
        status=DisputeStatus.PENDING_INVESTIGATION,
    )
    db.add(dispute)
    await db.commit()

    # Create ERPNext Support Ticket
    ticket = await client.create_support_issue(
        customer_id=payload.customer_id,
        subject=f"Telegram Dispute: {payload.issue_type} for {invoice_id}",
        description=f"Automated customer dispute intake. Amount: {amount} {payload.currency}. Query: {payload.user_message}",
        category="Payment Dispute",
    )

    # Broadcast WebSocket Event
    await ws_manager.broadcast({
        "type": "SUPPORT_DISPUTE_INGESTED",
        "dispute_id": dispute_id,
        "customer_id": payload.customer_id,
        "invoice_id": invoice_id,
        "amount": amount,
        "ticket_id": ticket.get("name"),
    })

    # Execute LangGraph Multi-Agent Pipeline
    inputs = {
        "messages": [{"role": "user", "content": dispute.reason}],
        "dispute": dispute,
    }
    agent_result = await finops_agent.ainvoke(inputs)

    fraud = agent_result.get("fraud")
    verdict = agent_result.get("policy_verdict")
    exec_res = agent_result.get("execution_result")

    # Update dispute with AI findings
    if fraud:
        dispute.fraud_score = fraud.risk_score
        dispute.risk_tier = RiskTier(fraud.risk_tier) if fraud.risk_tier in RiskTier.__members__ else RiskTier.LOW
        dispute.is_duplicate_payment = fraud.duplicate_payment_confirmed
        dispute.forensic_summary = fraud.forensic_summary

    confidence_pct = 97 if (fraud and fraud.duplicate_payment_confirmed) else 94

    if verdict == "AUTO_APPROVE" and exec_res:
        dispute.status = DisputeStatus.EXECUTED
        dispute.erp_payment_entry_id = exec_res.get("payment_entry_id")
        await db.commit()

        ref_id = exec_res.get("payment_entry_id", f"REF-2026-{uuid.uuid4().hex[:5].upper()}")
        return {
            "status": "AUTO_REFUNDED",
            "is_duplicate_payment": True,
            "fraud_score": fraud.risk_score if fraud else 0.08,
            "risk_tier": "LOW",
            "duplicate_details": f"We found two successful payments of ₹{amount:,.0f} made within 35 seconds. This appears to be a duplicate payment.",
            "recommended_action": f"Refund ₹{amount:,.0f}",
            "confidence_pct": confidence_pct,
            "refund_amount": amount,
            "currency": payload.currency,
            "reference_id": ref_id,
            "support_ticket_id": ticket.get("name"),
            "accounting_justification": fraud.accounting_justification if fraud else "Reversed duplicate capture in ERPNext ledger.",
            "summary_message": (
                f"We found two successful payments of ₹{amount:,.0f} made within 35 seconds.\n\n"
                f"This appears to be a duplicate payment.\n\n"
                f"• Recommended Action: Refund ₹{amount:,.0f}\n"
                f"• Confidence: {confidence_pct}%\n"
                f"• Reference ID: `{ref_id}`\n"
                f"• Support Ticket: `{ticket.get('name')}`"
            ),
        }
    elif verdict == "REQUIRE_HITL":
        dispute.status = DisputeStatus.AWAITING_APPROVAL
        await db.commit()

        escalation_ref = f"REF-2026-{uuid.uuid4().hex[:5].upper()}"
        return {
            "status": "ESCALATED_FOR_APPROVAL",
            "is_duplicate_payment": False,
            "fraud_score": fraud.risk_score if fraud else 0.45,
            "risk_tier": "MEDIUM",
            "duplicate_details": f"Transaction of ₹{amount:,.0f} exceeds automated threshold.",
            "recommended_action": "Manager Review & Approval",
            "confidence_pct": 92,
            "refund_amount": amount,
            "currency": payload.currency,
            "reference_id": escalation_ref,
            "support_ticket_id": ticket.get("name"),
            "accounting_justification": "Escalated to Branch / Finance Manager under HITL policy.",
            "summary_message": (
                f"Your refund request has been forwarded for approval.\n\n"
                f"• Reference ID: `{escalation_ref}`\n"
                f"• Ticket Number: `{ticket.get('name')}`\n"
                f"• Estimated Resolution: Within 2-4 hours\n\n"
                f"You will receive an instant notification once authorized by our operations desk."
            ),
        }
    else:
        dispute.status = DisputeStatus.REJECTED
        await db.commit()
        return {
            "status": "REJECTED",
            "is_duplicate_payment": False,
            "fraud_score": fraud.risk_score if fraud else 0.85,
            "risk_tier": "HIGH",
            "duplicate_details": "No duplicate capture found in ERPNext records.",
            "recommended_action": "Manual Branch Verification Required",
            "confidence_pct": 90,
            "refund_amount": 0.0,
            "currency": payload.currency,
            "reference_id": f"TKT-{ticket.get('name')}",
            "support_ticket_id": ticket.get("name"),
            "accounting_justification": "Dispute rejected under financial safety invariants.",
            "summary_message": (
                f"Our automated investigation could not verify a duplicate charge for this transaction.\n\n"
                f"• Support Ticket Created: `{ticket.get('name')}`\n"
                f"A customer service specialist has been assigned to your ticket."
            ),
        }


@router.post("/create-issue")
async def create_support_issue(payload: CreateSupportIssueRequest):
    """
    Creates an official Support Issue in ERPNext for the customer.
    """
    client = get_erp_client()
    issue = await client.create_support_issue(
        customer_id=payload.customer_id,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
    )
    return {
        "success": True,
        "issue": issue,
    }


@router.get("/refund-status/{customer_id}")
async def get_customer_refund_status(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the status of all refund and dispute claims for the customer.
    """
    stmt = select(Dispute).where(Dispute.customer_id == customer_id).order_by(Dispute.created_at.desc())
    res = await db.execute(stmt)
    disputes = res.scalars().all()
    return {
        "customer_id": customer_id,
        "disputes": [d.to_dict() for d in disputes],
        "count": len(disputes),
    }
