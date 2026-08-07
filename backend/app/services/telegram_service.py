import asyncio
import logging
import uuid
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.models.approval import ApprovalRequest
from backend.app.services.audit_service import AuditService
from backend.app.services.erpnext_mock import get_erp_client
from backend.app.schemas.erp import ERPPaymentEntryCreate, ERPPaymentEntryReference
from backend.app.api.v1.websocket import ws_manager
from agents.graph import finops_agent
from agents.models.fast_classifier import FastEntityExtractor

logger = logging.getLogger("FinOpsTelegram")

bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

if settings.TELEGRAM_BOT_TOKEN and not settings.TELEGRAM_BOT_TOKEN.startswith("your_"):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        dp = Dispatcher()
        logger.info("Telegram Bot successfully configured.")
    except Exception as e:
        logger.warning("Failed to initialize Telegram Bot: %s", e)


def get_manager_approval_keyboard(dispute_id: str, amount: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"✅ Approve ${amount:.2f}", callback_data=f"app:{dispute_id}:APPROVED"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"app:{dispute_id}:REJECTED"),
            ],
            [
                InlineKeyboardButton(text="🔍 View in React Ops Hub", url="http://localhost:3000"),
            ],
        ]
    )


if dp:
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            "💼 *Agentic Financial Operations Assistant (FinOps AI)*\n\n"
            "I am your autonomous enterprise financial operations employee integrated with *ERPNext*.\n\n"
            "You can message me directly with any payment disputes, duplicate charges, or invoice issues.\n\n"
            "_Example_: `Hi, I was double charged for invoice INV-2026-001 ($150.00).`",
            parse_mode="Markdown",
        )

    @dp.message(F.text)
    async def handle_customer_message(message: types.Message):
        user_text = message.text
        extracted = FastEntityExtractor.extract_entities(user_text)
        invoice_id = extracted.get("invoice_id") or "INV-2026-001"
        amount = extracted.get("amount") or 150.00
        dispute_id = f"DISP-{invoice_id}-{uuid.uuid4().hex[:6].upper()}"

        # 1. Immediate Customer Feedback
        status_msg = await message.answer(
            f"🔍 *Locating invoice `{invoice_id}` in ERPNext System of Record...*\n"
            f"Running multi-factor forensic fraud analysis...",
            parse_mode="Markdown",
        )

        # 2. Database Record & LangGraph Execution
        async with AsyncSessionLocal() as session:
            # Create unique dispute record
            dispute = Dispute(
                id=dispute_id,
                customer_id="CUST-001",
                invoice_id=invoice_id,
                amount=amount,
                currency="USD",
                reason=user_text,
                status=DisputeStatus.PENDING_INVESTIGATION,
            )
            session.add(dispute)
            await session.commit()

            # Broadcast WebSocket Event
            await ws_manager.broadcast({
                "type": "DISPUTE_INGESTED",
                "dispute_id": dispute_id,
                "invoice_id": invoice_id,
                "amount": amount,
                "channel": "TELEGRAM",
            })

            # Run LangGraph State Machine
            inputs = {
                "messages": [{"role": "user", "content": user_text}],
                "dispute": dispute,
            }
            agent_result = await finops_agent.ainvoke(inputs)
            
            fraud = agent_result.get("fraud")
            verdict = agent_result.get("policy_verdict")
            exec_res = agent_result.get("execution_result")

            # Update DB with AI findings
            if fraud:
                dispute.fraud_score = fraud.risk_score
                dispute.risk_tier = RiskTier(fraud.risk_tier) if fraud.risk_tier in RiskTier.__members__ else RiskTier.LOW
                dispute.is_duplicate_payment = fraud.duplicate_payment_confirmed
                dispute.forensic_summary = fraud.forensic_summary

            if verdict == "AUTO_APPROVE" and exec_res:
                dispute.status = DisputeStatus.EXECUTED
                dispute.erp_payment_entry_id = exec_res.get("payment_entry_id")
                await session.commit()

                # Broadcast live update
                await ws_manager.broadcast({
                    "type": "REFUND_AUTO_EXECUTED",
                    "dispute_id": dispute_id,
                    "payment_entry": exec_res.get("payment_entry_id"),
                    "amount": amount,
                    "risk_score": fraud.risk_score if fraud else 0.08,
                })

                await status_msg.edit_text(
                    f"✅ *Payment Dispute Resolved & Refunded*\n\n"
                    f"• *Invoice*: `{invoice_id}`\n"
                    f"• *Refund Amount*: `${amount:.2f} USD`\n"
                    f"• *ERPNext Payment Entry*: `{exec_res.get('payment_entry_id')}`\n"
                    f"• *Risk Score*: `{fraud.risk_score:.2f}` (Safe / Verified Duplicate)\n"
                    f"• *Ledger Status*: `Debtors Ledger 2110 Credited`\n\n"
                    f"Your refund has been executed in the System of Record and credited back to your payment method.",
                    parse_mode="Markdown",
                )
            elif verdict == "REQUIRE_HITL":
                dispute.status = DisputeStatus.AWAITING_APPROVAL
                await session.commit()

                # Broadcast live update
                await ws_manager.broadcast({
                    "type": "HITL_ESCALATION_TRIGGERED",
                    "dispute_id": dispute_id,
                    "amount": amount,
                    "risk_score": fraud.risk_score if fraud else 0.45,
                })

                # Notify Customer of review
                await status_msg.edit_text(
                    f"⏱️ *Dispute Under Management Review*\n\n"
                    f"Your claim for Invoice `{invoice_id}` (${amount:.2f}) is being verified by our finance operations desk. "
                    f"You will receive an instant notification once authorized.",
                    parse_mode="Markdown",
                )

                # Push Interactive HITL Card to Manager
                manager_chat_id = settings.TELEGRAM_MANAGER_CHAT_ID or message.chat.id
                await bot.send_message(
                    chat_id=manager_chat_id,
                    text=(
                        f"🚨 *ACTION REQUIRED: Financial Operation Approval*\n\n"
                        f"• *Dispute ID*: `{dispute_id}`\n"
                        f"• *Customer*: `Acme Corp (CUST-001)`\n"
                        f"• *Invoice*: `{invoice_id}`\n"
                        f"• *Requested Refund*: *${amount:.2f} USD*\n"
                        f"• *Risk Score*: *{fraud.risk_score if fraud else 0.45:.2f}*\n"
                        f"• *Forensic Summary*: {fraud.forensic_summary if fraud else 'High-value threshold'}\n\n"
                        f"*Select an action to execute in ERPNext:*",
                    ),
                    reply_markup=get_manager_approval_keyboard(dispute_id, amount),
                    parse_mode="Markdown",
                )
            else:
                dispute.status = DisputeStatus.REJECTED
                await session.commit()
                await status_msg.edit_text(
                    f"❌ *Dispute Rejected by Financial Policy*\n\n"
                    f"Reason: {agent_result.get('policy_reason') or 'Risk score exceeded safety boundaries.'}",
                    parse_mode="Markdown",
                )

    @dp.callback_query(F.data.startswith("app:"))
    async def handle_manager_callback(query: types.CallbackQuery):
        _, dispute_id, decision = query.data.split(":")
        await query.answer(f"Processing {decision} in ERPNext...")

        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(Dispute).where(Dispute.id == dispute_id)
            res = await session.execute(stmt)
            dispute = res.scalar_one_or_none()
            if not dispute:
                return

            if decision == "APPROVED":
                erp_client = get_erp_client()
                refund_payload = ERPPaymentEntryCreate(
                    payment_type="Pay",
                    party_type="Customer",
                    party=dispute.customer_id,
                    paid_amount=dispute.amount,
                    received_amount=dispute.amount,
                    reference_no=f"TG-HITL-{dispute_id}",
                    reference_date="2026-08-08",
                    references=[
                        ERPPaymentEntryReference(
                            reference_doctype="Sales Invoice",
                            reference_name=dispute.invoice_id,
                            allocated_amount=dispute.amount,
                        )
                    ],
                    remarks=f"Telegram 1-Click Manager Approval (User: {query.from_user.id})",
                )
                erp_res = await erp_client.create_refund_payment(refund_payload)
                dispute.status = DisputeStatus.EXECUTED
                dispute.erp_payment_entry_id = erp_res.get("name")
                
                await AuditService.record_event(
                    session=session,
                    dispute_id=dispute_id,
                    action="TELEGRAM_MANAGER_APPROVED",
                    agent_node="TelegramHITLBridge",
                    justification=f"Approved by Manager {query.from_user.username or query.from_user.id} via Telegram Inline Keyboard.",
                    state_diff={"erp_payment_entry": erp_res.get("name")},
                )
                await session.commit()

                await ws_manager.broadcast({
                    "type": "HITL_APPROVED",
                    "dispute_id": dispute_id,
                    "payment_entry": erp_res.get("name"),
                    "amount": dispute.amount,
                })

                await query.message.edit_text(
                    f"✅ *APPROVED & EXECUTED IN ERPNEXT*\n\n"
                    f"• *Dispute ID*: `{dispute_id}`\n"
                    f"• *Amount Refunded*: `${dispute.amount:.2f} USD`\n"
                    f"• *ERPNext Payment Entry*: `{erp_res.get('name')}`\n"
                    f"• *Authorized By*: @{query.from_user.username or 'Manager'}\n"
                    f"• *Status*: `Ledger Entry Posted Successfully`",
                    parse_mode="Markdown",
                )
            else:
                dispute.status = DisputeStatus.REJECTED
                await AuditService.record_event(
                    session=session,
                    dispute_id=dispute_id,
                    action="TELEGRAM_MANAGER_REJECTED",
                    agent_node="TelegramHITLBridge",
                    justification=f"Rejected by Manager {query.from_user.username or query.from_user.id} via Telegram.",
                )
                await session.commit()

                await ws_manager.broadcast({
                    "type": "HITL_REJECTED",
                    "dispute_id": dispute_id,
                })

                await query.message.edit_text(
                    f"❌ *REJECTED BY MANAGER*\n\n"
                    f"• *Dispute ID*: `{dispute_id}`\n"
                    f"• *Amount*: `${dispute.amount:.2f}`\n"
                    f"• *Action*: Request cancelled. Zero ledger entry created.",
                    parse_mode="Markdown",
                )


async def start_telegram_bot():
    """Starts the Telegram bot in background async task."""
    if bot and dp:
        logger.info("Starting Telegram Bot Polling service...")
        asyncio.create_task(dp.start_polling(bot))
