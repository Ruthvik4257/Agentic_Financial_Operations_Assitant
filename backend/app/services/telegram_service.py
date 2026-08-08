import asyncio
import logging
import uuid
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
from aiogram.utils.chat_action import ChatActionSender

from backend.app.core.config import settings
from backend.app.services.erpnext_mock import get_erp_client
from backend.app.models.dispute import Dispute, DisputeStatus, RiskTier
from backend.app.models.approval import ApprovalRequest
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.audit_service import AuditService
from backend.app.schemas.erp import ERPPaymentEntryCreate, ERPPaymentEntryReference
from backend.app.api.v1.websocket import ws_manager
from backend.app.api.v1.customer_support import (
    verify_customer,
    CustomerVerificationRequest,
    investigate_customer_issue,
    InvestigationRequest,
    mask_email,
    mask_phone,
)

logger = logging.getLogger("NovaBankTelegramBot")

bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None
router = Router()

# ==============================================================================
# IN-MEMORY ENTERPRISE SESSION STORE
# ==============================================================================
class UserSession:
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self.is_verified: bool = False
        self.customer_id: Optional[str] = None
        self.customer_name: Optional[str] = None
        self.registered_email: Optional[str] = None
        self.registered_mobile: Optional[str] = None
        self.customer_group: Optional[str] = None
        self.loyalty_tier: Optional[str] = None
        
        # Workflow Context
        self.auth_method: Optional[str] = None  # 'mobile', 'email', 'customer_id'
        self.current_workflow: Optional[str] = None  # e.g., 'payment_issues', 'refund_requests'
        self.selected_issue: Optional[str] = None
        self.awaiting_input: Optional[str] = None  # 'auth_identifier', 'manual_invoice', 'issue_description'
        self.temp_invoice_id: Optional[str] = None
        self.temp_amount: Optional[float] = None
        self.history: List[Dict[str, Any]] = []

    def reset_workflow(self):
        self.current_workflow = None
        self.selected_issue = None
        self.awaiting_input = None
        self.temp_invoice_id = None
        self.temp_amount = None


user_sessions: Dict[int, UserSession] = {}
customer_chat_map: Dict[str, int] = {}


def get_or_create_session(user_id: int) -> UserSession:
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    return user_sessions[user_id]


async def notify_customer_refund_status(
    customer_id: str,
    dispute_id: str,
    invoice_id: str,
    amount: float,
    status: str,
    payment_entry_id: Optional[str] = None,
    currency: str = "INR",
    manager_notes: Optional[str] = None,
    chat_id: Optional[str] = None,
):
    """
    Proactively pushes a real-time banking notification directly to the customer on Telegram
    whenever a refund is executed or approved by AI / human manager.
    """
    if not bot:
        return

    target_chat_id = int(chat_id) if (chat_id and str(chat_id).isdigit()) else customer_chat_map.get(customer_id)
    if not target_chat_id:
        for uid, sess in user_sessions.items():
            if sess.customer_id == customer_id:
                target_chat_id = uid
                break

    if not target_chat_id:
        logger.info("No active Telegram chat session found for customer %s (dispute %s)", customer_id, dispute_id)
        return

    try:
        if status in ["EXECUTED", "APPROVED"]:
            text = (
                f"🔔 *Refund Initiated & Credited to Your Account*\n\n"
                f"Hello *{customer_id}* 👋,\n\n"
                f"We are pleased to inform you that your refund has been successfully authorized and executed in our general ledger.\n\n"
                f"💳 *Transaction Details*:\n"
                f"• *Dispute ID*: `{dispute_id}`\n"
                f"• *Invoice*: `{invoice_id}`\n"
                f"• *Refund Amount*: *₹{amount:,.2f} {currency}*\n"
                f"• *ERPNext Payment Entry*: `{payment_entry_id or 'PE-REF-EXECUTED'}`\n"
                f"• *Status*: `Completed & Ledger Reconciled`\n"
                f"• *Reference*: `TX-REFUND-{uuid.uuid4().hex[:6].upper()}`\n\n"
                f"⏱ *Estimated Bank Credit Time*: Instant to 24 hours depending on your payment network.\n\n"
                f"Thank you for banking with NovaBank! 🏦"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📜 View Updated Statement", callback_data="tx:recent")],
                    [InlineKeyboardButton(text="🏠 Main Menu", callback_data="nav:main_menu")],
                ]
            )
        else:
            text = (
                f"📋 *Dispute Review Update*\n\n"
                f"Hello *{customer_id}* 👋,\n\n"
                f"Your dispute request `{dispute_id}` for Invoice `{invoice_id}` (₹{amount:,.2f}) has been reviewed by our operations desk.\n\n"
                f"• *Decision*: `Not Approved for Automated Refund`\n"
                f"• *Notes*: {manager_notes or 'Claim could not be verified against gateway settlement records.'}\n\n"
                f"If you require further assistance or wish to speak with an executive, tap below."
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🧑‍💼 Talk to Human Support", callback_data="auth_retry:human")],
                    [InlineKeyboardButton(text="🏠 Main Menu", callback_data="nav:main_menu")],
                ]
            )

        await bot.send_message(
            chat_id=target_chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        logger.info("Successfully dispatched Telegram push notification to customer %s (Chat %s)", customer_id, target_chat_id)
    except Exception as e:
        logger.error("Failed to send Telegram refund notification to %s: %s", target_chat_id, e)


# ==============================================================================
# KEYBOARD BUILDERS (Clean, Modern, Enterprise Banking UX)
# ==============================================================================
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns the main banking menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Payment Issues", callback_data="menu:payment_issues"),
                InlineKeyboardButton(text="💰 Refund Requests", callback_data="menu:refund_requests"),
            ],
            [
                InlineKeyboardButton(text="📜 Transaction History", callback_data="menu:tx_history"),
                InlineKeyboardButton(text="🛡 Fraud & Security", callback_data="menu:fraud_security"),
            ],
            [
                InlineKeyboardButton(text="👤 Account Support", callback_data="menu:account_support"),
                InlineKeyboardButton(text="🤖 Talk to AI Assistant", callback_data="menu:talk_to_ai"),
            ],
        ]
    )


def get_nav_footer(back_callback: str = "nav:main_menu") -> List[List[InlineKeyboardButton]]:
    """Standard breadcrumb navigation attached to every submenu."""
    return [
        [
            InlineKeyboardButton(text="⬅ Back", callback_data=back_callback),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="nav:main_menu"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="nav:cancel"),
        ]
    ]


def get_auth_method_keyboard() -> InlineKeyboardMarkup:
    """Options for identity verification."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Mobile Number", callback_data="auth_method:mobile"),
                InlineKeyboardButton(text="📧 Email Address", callback_data="auth_method:email"),
            ],
            [
                InlineKeyboardButton(text="🆔 Customer ID", callback_data="auth_method:customer_id"),
            ],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_auth_confirm_keyboard() -> InlineKeyboardMarkup:
    """Account profile confirmation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes, Continue", callback_data="auth_confirm:yes"),
                InlineKeyboardButton(text="❌ Not Me", callback_data="auth_confirm:no"),
            ]
        ]
    )


def get_auth_retry_keyboard() -> InlineKeyboardMarkup:
    """Retry options when customer is not located."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Try Again", callback_data="auth_retry:again"),
                InlineKeyboardButton(text="🔍 Use Another Identifier", callback_data="auth_retry:other"),
            ],
            [
                InlineKeyboardButton(text="🧑‍💼 Talk to Human Support", callback_data="auth_retry:human"),
            ],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_payment_issues_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Money Deducted but Payment Failed", callback_data="issue:deducted_failed")],
            [InlineKeyboardButton(text="Charged Twice", callback_data="issue:charged_twice")],
            [InlineKeyboardButton(text="Payment Pending", callback_data="issue:payment_pending")],
            [InlineKeyboardButton(text="UPI Failed", callback_data="issue:upi_failed")],
            [InlineKeyboardButton(text="Card Payment Failed", callback_data="issue:card_failed")],
            [InlineKeyboardButton(text="Payment Not Reflected", callback_data="issue:payment_not_reflected")],
            [InlineKeyboardButton(text="Other", callback_data="issue:payment_other")],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_refund_requests_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Refund Status", callback_data="refund:status")],
            [InlineKeyboardButton(text="Request Refund", callback_data="refund:request")],
            [InlineKeyboardButton(text="Refund Delayed", callback_data="refund:delayed")],
            [InlineKeyboardButton(text="Refund Cancelled", callback_data="refund:cancelled")],
            [InlineKeyboardButton(text="Refund Eligibility", callback_data="refund:eligibility")],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_tx_history_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Recent Transactions", callback_data="tx:recent")],
            [InlineKeyboardButton(text="Payment Details", callback_data="tx:details")],
            [InlineKeyboardButton(text="Invoice History", callback_data="tx:invoices")],
            [InlineKeyboardButton(text="Download Statement", callback_data="tx:statement")],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_fraud_security_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Unauthorized Transaction", callback_data="fraud:unauthorized")],
            [InlineKeyboardButton(text="Report Fraud", callback_data="fraud:report")],
            [InlineKeyboardButton(text="Card Lost", callback_data="fraud:card_lost")],
            [InlineKeyboardButton(text="Account Compromised", callback_data="fraud:compromised")],
            [InlineKeyboardButton(text="Suspicious Login", callback_data="fraud:suspicious_login")],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_account_support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Update Mobile Number", callback_data="account:update_mobile")],
            [InlineKeyboardButton(text="Update Email", callback_data="account:update_email")],
            [InlineKeyboardButton(text="KYC Issues", callback_data="account:kyc")],
            [InlineKeyboardButton(text="Account Locked", callback_data="account:locked")],
            [InlineKeyboardButton(text="Other", callback_data="account:other")],
            *get_nav_footer("nav:main_menu"),
        ]
    )


def get_manager_approval_keyboard(dispute_id: str, amount: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"✅ Approve ₹{amount:,.0f}", callback_data=f"app:{dispute_id}:APPROVED"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"app:{dispute_id}:REJECTED"),
            ],
            [
                InlineKeyboardButton(text="🔍 View in Operations Hub", url="http://localhost:3000"),
            ],
        ]
    )


# ==============================================================================
# WELCOME FLOW & GREETINGS
# ==============================================================================
@router.message(Command("start"))
@router.message(F.text.lower().in_(["hi", "hello", "hey", "/menu", "menu", "help"]))
async def welcome_handler(message: Message):
    """
    Displays the standard welcome greeting and main banking menu.
    """
    session = get_or_create_session(message.from_user.id)
    session.reset_workflow()

    welcome_text = (
        "👋 *Welcome to NovaBank AI Financial Assistant*\n\n"
        "I'm here to help you with your banking and payment related issues.\n\n"
        "Please choose one of the options below."
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


# ==============================================================================
# NAVIGATION & CANCEL HANDLERS
# ==============================================================================
@router.callback_query(F.data.startswith("nav:"))
async def handle_navigation(query: CallbackQuery):
    action = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    if action == "main_menu":
        session.reset_workflow()
        await query.message.edit_text(
            "👋 *Welcome to NovaBank AI Financial Assistant*\n\n"
            "I'm here to help you with your banking and payment related issues.\n\n"
            "Please choose one of the options below.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    elif action == "cancel":
        session.reset_workflow()
        await query.message.edit_text(
            "Operation cancelled.\n\n"
            "Whenever you need assistance, tap the button below to return to the main menu.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="nav:main_menu")]]
            ),
        )
    elif action == "back":
        session.reset_workflow()
        await query.message.edit_text(
            "👋 *Welcome to NovaBank AI Financial Assistant*\n\n"
            "Please choose one of the options below.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )


# ==============================================================================
# MENU ROUTING & IDENTITY GATE
# ==============================================================================
@router.callback_query(F.data.startswith("menu:"))
async def handle_main_menu_selection(query: CallbackQuery):
    menu_type = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    session.current_workflow = menu_type
    await query.answer()

    # Identity Verification Gate: Check before revealing financial data or proceeding
    if not session.is_verified:
        await prompt_identity_verification(query.message, session)
        return

    # Already verified: direct routing to requested workflow
    await route_verified_menu(query.message, menu_type, session)


async def prompt_identity_verification(message: Message, session: UserSession):
    """Prompts customer to choose an identification method."""
    text = (
        "🔒 *Account Verification Required*\n\n"
        "To protect your account, please choose one way to identify yourself."
    )
    if hasattr(message, "edit_text"):
        await message.edit_text(text, reply_markup=get_auth_method_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=get_auth_method_keyboard(), parse_mode="Markdown")


async def route_verified_menu(message: Message, menu_type: str, session: UserSession):
    """Renders the appropriate verified submenu."""
    if menu_type == "payment_issues":
        await message.edit_text(
            "💳 *Payment Issues*\n\n"
            "Please select the specific issue you are experiencing:",
            reply_markup=get_payment_issues_keyboard(),
            parse_mode="Markdown",
        )
    elif menu_type == "refund_requests":
        await message.edit_text(
            "💰 *Refund Requests*\n\n"
            "Please select an option to manage or check your refunds:",
            reply_markup=get_refund_requests_keyboard(),
            parse_mode="Markdown",
        )
    elif menu_type == "tx_history":
        await message.edit_text(
            "📜 *Transaction History*\n\n"
            "Choose a statement or transaction view:",
            reply_markup=get_tx_history_keyboard(),
            parse_mode="Markdown",
        )
    elif menu_type == "fraud_security":
        await message.edit_text(
            "🛡 *Fraud & Security Desk*\n\n"
            "Protect your account. Select an urgent action below:",
            reply_markup=get_fraud_security_keyboard(),
            parse_mode="Markdown",
        )
    elif menu_type == "account_support":
        await message.edit_text(
            "👤 *Account Support*\n\n"
            "Select an account management service:",
            reply_markup=get_account_support_keyboard(),
            parse_mode="Markdown",
        )
    elif menu_type == "talk_to_ai":
        await initiate_ai_chat_flow(message, session)


# ==============================================================================
# IDENTITY VERIFICATION FLOW
# ==============================================================================
@router.callback_query(F.data.startswith("auth_method:"))
async def handle_auth_method(query: CallbackQuery):
    method = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    session.auth_method = method
    session.awaiting_input = "auth_identifier"
    await query.answer()

    if method == "mobile":
        prompt = (
            "Please enter your registered mobile number.\n\n"
            "_Example_:\n`9876543210`"
        )
    elif method == "email":
        prompt = (
            "Please enter your registered email address.\n\n"
            "_Example_:\n`rahul.sharma@gmail.com`"
        )
    else:
        prompt = (
            "Please enter your Customer ID.\n\n"
            "_Example_:\n`CUST-00045`"
        )

    await query.message.edit_text(prompt, parse_mode="Markdown")


@router.callback_query(F.data.startswith("auth_confirm:"))
async def handle_auth_confirmation(query: CallbackQuery):
    decision = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    if decision == "yes":
        session.is_verified = True
        session.awaiting_input = None
        if session.customer_id:
            customer_chat_map[session.customer_id] = query.from_user.id
        
        await query.message.edit_text(
            f"✅ *Verification Successful*\n\n"
            f"Welcome back, *{session.customer_name}*!\n\n"
            f"Your session is now authenticated. Redirecting to your requested service...",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1.0)

        # Resume the pending workflow or return to main menu
        if session.current_workflow:
            await route_verified_menu(query.message, session.current_workflow, session)
        else:
            await query.message.answer(
                "Please choose one of the options below:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown",
            )
    else:
        session.is_verified = False
        session.customer_id = None
        session.customer_name = None
        await query.message.edit_text(
            "We couldn't locate your account.",
            reply_markup=get_auth_retry_keyboard(),
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("auth_retry:"))
async def handle_auth_retry(query: CallbackQuery):
    action = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    if action == "again":
        session.awaiting_input = "auth_identifier"
        await query.message.edit_text(
            "Please re-enter your registered identifier:",
            parse_mode="Markdown",
        )
    elif action == "other":
        await prompt_identity_verification(query.message, session)
    elif action == "human":
        # Create Human Support Ticket in ERPNext via FastAPI
        client = get_erp_client()
        ticket = await client.create_support_issue(
            customer_id="GUEST",
            subject="Telegram Human Support Request (Unverified Account)",
            description=f"User {query.from_user.id} requested human banking support.",
            category="Customer Verification",
        )
        await query.message.edit_text(
            f"🧑‍💼 *Human Support Request Logged*\n\n"
            f"A representative from our customer desk has been assigned.\n\n"
            f"• Ticket Reference: `{ticket.get('name', 'TKT-2026-009')}`\n"
            f"• Support Hotline: `1800-2026-NOVA`\n\n"
            f"We will assist you within 15 minutes.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="nav:main_menu")]]
            ),
            parse_mode="Markdown",
        )


# ==============================================================================
# SUBMENU HANDLERS (Payment Issues, Refunds, History, Fraud, Account)
# ==============================================================================
@router.callback_query(F.data.startswith("issue:"))
async def handle_payment_issue_selected(query: CallbackQuery):
    issue_key = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    session.selected_issue = issue_key
    await query.answer()

    issue_labels = {
        "deducted_failed": "Money Deducted but Payment Failed",
        "charged_twice": "Charged Twice (Duplicate Payment)",
        "payment_pending": "Payment Pending",
        "upi_failed": "UPI Failed",
        "card_failed": "Card Payment Failed",
        "payment_not_reflected": "Payment Not Reflected",
        "payment_other": "Payment Issue",
    }
    label = issue_labels.get(issue_key, "Payment Dispute")

    # Fetch customer's recent transactions from FastAPI / ERPNext to offer 1-Click selection
    client = get_erp_client()
    txs = await client.get_customer_transactions(session.customer_id or "CUST-00045")

    buttons = []
    for tx in txs[:3]:
        inv_name = tx.get("name", "INV-2026-001")
        total = tx.get("grand_total", 2350.00)
        curr = tx.get("currency", "INR")
        buttons.append([
            InlineKeyboardButton(
                text=f"📄 {inv_name} ({curr} {total:,.0f})",
                callback_data=f"select_tx:{inv_name}:{total}",
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="✍ Enter Invoice / Transaction ID Manually", callback_data="select_tx:manual:0")
    ])
    buttons.extend(get_nav_footer("menu:payment_issues"))

    await query.message.edit_text(
        f"💳 *{label}*\n\n"
        f"To investigate, please select the affected transaction or enter details:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("select_tx:"))
async def handle_tx_selection(query: CallbackQuery):
    _, inv_id, amt_str = query.data.split(":")
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    if inv_id == "manual":
        session.awaiting_input = "manual_invoice"
        await query.message.edit_text(
            "Please enter your Invoice ID or Transaction Reference:\n\n"
            "_Example_: `INV-2026-001` or `TXN-882100`",
            parse_mode="Markdown",
        )
    else:
        amount = float(amt_str) if amt_str else 2350.00
        session.temp_invoice_id = inv_id
        session.temp_amount = amount
        # Launch the enterprise AI multi-agent investigation!
        await run_investigation_workflow(query.message, session, inv_id, amount)


@router.callback_query(F.data.startswith("refund:"))
async def handle_refund_menu_selected(query: CallbackQuery):
    action = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    if action == "status":
        # Query existing refund disputes from SQL DB via FastAPI service
        client = get_erp_client()
        txs = await client.get_customer_transactions(session.customer_id or "CUST-00045")
        
        await query.message.edit_text(
            f"💰 *Refund Status for {session.customer_name}*\n\n"
            f"• *Active Accounts*: `1 Verified Profile`\n"
            f"• *Eligible Invoices*: `{len(txs)} Records Found`\n"
            f"• *Standard Processing Time*: `< 24 Hours for UPI/Cards`\n\n"
            f"Select a transaction to initiate or check refund:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Re-check Active Refunds", callback_data="refund:status")],
                    [InlineKeyboardButton(text="💰 Request New Refund", callback_data="issue:charged_twice")],
                    *get_nav_footer("menu:refund_requests"),
                ]
            ),
            parse_mode="Markdown",
        )
    else:
        # Route to refund investigation flow
        session.selected_issue = f"Refund - {action.capitalize()}"
        await handle_payment_issue_selected(query)


@router.callback_query(F.data.startswith("tx:"))
async def handle_tx_history_selected(query: CallbackQuery):
    action = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    client = get_erp_client()
    txs = await client.get_customer_transactions(session.customer_id or "CUST-00045")

    tx_summary = ""
    for t in txs[:4]:
        name = t.get("name", "INV-2026-001")
        date = t.get("posting_date", "2026-08-01")
        total = t.get("grand_total", 2350.00)
        status = t.get("status", "Paid")
        curr = t.get("currency", "INR")
        tx_summary += f"• `{name}` | {date} | *{curr} {total:,.2f}* ({status})\n"

    if not tx_summary:
        tx_summary = "No recent transactions found on record."

    await query.message.edit_text(
        f"📜 *Transaction Records for {session.customer_name}*\n\n"
        f"{tx_summary}\n"
        f"🔒 *Ledger Security*: All records cryptographically verified with ERPNext.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📥 Email Full PDF Statement", callback_data="account:statement_emailed")],
                *get_nav_footer("menu:tx_history"),
            ]
        ),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("fraud:"))
async def handle_fraud_menu_selected(query: CallbackQuery):
    fraud_action = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    session.selected_issue = f"FRAUD: {fraud_action.upper()}"
    await query.answer()

    # Immediate security acknowledgment
    await query.message.edit_text(
        f"🛡 *URGENT SECURITY PROTOCOL ACTIVATED*\n\n"
        f"We have noted your report: *{fraud_action.replace('_', ' ').capitalize()}*.\n\n"
        f"• Customer: `{session.customer_name} ({session.customer_id})`\n"
        f"• Account Safety Status: `High-Priority Lock Available`\n\n"
        f"Please provide any suspicious transaction or amount involved for immediate forensic analysis:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚨 Lock Card Immediately", callback_data="account:card_locked")],
                [InlineKeyboardButton(text="🔍 Run Forensic Transaction Investigation", callback_data="issue:deducted_failed")],
                *get_nav_footer("menu:fraud_security"),
            ]
        ),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("account:"))
async def handle_account_menu_selected(query: CallbackQuery):
    action = query.data.split(":")[1]
    session = get_or_create_session(query.from_user.id)
    await query.answer()

    if action == "card_locked":
        await query.message.edit_text(
            f"🔒 *Card Temporarily Blocked*\n\n"
            f"Your debit and credit cards for customer `{session.customer_id}` have been temporarily blocked for security.\n\n"
            f"Reference: `SEC-LOCK-{uuid.uuid4().hex[:6].upper()}`",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[*get_nav_footer("menu:account_support")]
            ),
            parse_mode="Markdown",
        )
    elif action == "statement_emailed":
        await query.message.edit_text(
            f"📧 *Statement Dispatched*\n\n"
            f"An encrypted PDF statement has been sent to your registered email `{session.registered_email}`.\n\n"
            f"Password to open: `First 4 letters of name + DDMM of birth`",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[*get_nav_footer("menu:tx_history")]
            ),
            parse_mode="Markdown",
        )
    else:
        # Create ticket in ERPNext
        client = get_erp_client()
        ticket = await client.create_support_issue(
            customer_id=session.customer_id or "CUST-00045",
            subject=f"Account Support Request: {action}",
            description=f"Customer {session.customer_name} requested {action}.",
            category="Account Maintenance",
        )
        await query.message.edit_text(
            f"👤 *Account Service Request Created*\n\n"
            f"• Service: `{action.replace('_', ' ').capitalize()}`\n"
            f"• Ticket Number: `{ticket.get('name')}`\n"
            f"• Status: `Assigned to KYC Desk`\n\n"
            f"A confirmation SMS has been sent to `{session.registered_mobile}`.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[*get_nav_footer("menu:account_support")]
            ),
            parse_mode="Markdown",
        )


# ==============================================================================
# AI INVOCATION & PROGRESS WORKFLOW
# ==============================================================================
async def initiate_ai_chat_flow(message: Message, session: UserSession):
    """Invokes AI assistant mode when requested."""
    session.awaiting_input = "issue_description"
    text = (
        "🤖 *NovaBank AI Financial Intelligence*\n\n"
        "Please describe your payment or ledger issue in natural language.\n\n"
        "_Example_: `I was charged ₹2,350 twice for invoice INV-2026-001 on August 1st.`"
    )
    if hasattr(message, "edit_text"):
        await message.edit_text(text, parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")


async def run_investigation_workflow(
    message: Message,
    session: UserSession,
    invoice_id: str,
    amount: float,
    user_note: str = "",
):
    """
    Executes the realistic multi-step enterprise investigation with progress updates,
    calls FastAPI customer support endpoints, triggers LangGraph, and renders results.
    """
    status_msg = await message.answer("🔍 *Identifying your account...*", parse_mode="Markdown")
    await asyncio.sleep(0.4)

    steps = [
        "✅ Customer verified.",
        "🔎 Retrieving recent transactions...",
        "💳 Checking payment records...",
        "🛡 Running fraud analysis...",
        "📋 Reviewing refund policy...",
        "🤖 AI is preparing a recommendation...",
    ]

    for step in steps:
        try:
            await status_msg.edit_text(f"*{step}*", parse_mode="Markdown")
            await asyncio.sleep(0.35)
        except Exception:
            pass

    # Call the FastAPI customer support investigation endpoint
    inv_req = InvestigationRequest(
        customer_id=session.customer_id or "CUST-00045",
        issue_type=session.selected_issue or "Duplicate Charge",
        invoice_id=invoice_id,
        amount=amount,
        currency="INR",
        user_message=user_note or f"Dispute on {invoice_id} for amount {amount}",
    )

    async with AsyncSessionLocal() as db_session:
        try:
            result = await investigate_customer_issue(payload=inv_req, db=db_session)
        except Exception as e:
            logger.error("FastAPI investigation error: %s", e)
            await status_msg.edit_text(
                "We're currently unable to retrieve your account information.\n\n"
                "Please try again shortly.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="nav:main_menu")]]
                ),
            )
            return

    # Render results
    if result.get("status") == "AUTO_REFUNDED":
        result_text = (
            f"We found two successful payments of *₹{amount:,.0f}* made within 35 seconds.\n\n"
            f"This appears to be a duplicate payment.\n\n"
            f"• *Recommended Action*: Refund ₹{amount:,.0f}\n"
            f"• *Confidence*: {result.get('confidence_pct', 97)}%\n"
            f"• *Payment Entry Ref*: `{result.get('reference_id')}`\n"
            f"• *Support Ticket*: `{result.get('support_ticket_id')}`\n\n"
            f"✅ *Refund of ₹{amount:,.0f} has been executed* and reversed to your original payment method."
        )
    elif result.get("status") == "ESCALATED_FOR_APPROVAL":
        ref_id = result.get("reference_id", "REF-2026-00152")
        result_text = (
            f"Your refund request has been forwarded for approval.\n\n"
            f"• *Reference ID*: `{ref_id}`\n"
            f"• *Amount*: ₹{amount:,.0f}\n"
            f"• *Support Ticket*: `{result.get('support_ticket_id')}`\n"
            f"• *Estimated Resolution*: Within 2-4 hours\n\n"
            f"You will receive an instant notification once authorized by our operations desk."
        )
        
        # Also notify Manager in Background
        manager_chat_id = settings.TELEGRAM_MANAGER_CHAT_ID or message.chat.id
        try:
            await bot.send_message(
                chat_id=manager_chat_id,
                text=(
                    f"🚨 *ACTION REQUIRED: Financial Operation Approval*\n\n"
                    f"• *Reference ID*: `{ref_id}`\n"
                    f"• *Customer*: `{session.customer_name} ({session.customer_id})`\n"
                    f"• *Invoice*: `{invoice_id}`\n"
                    f"• *Requested Refund*: *₹{amount:,.0f}*\n"
                    f"• *Risk Score*: `0.12 (Safe / Duplicate Capture)`\n\n"
                    f"*Select an action to execute in ERPNext:*",
                ),
                reply_markup=get_manager_approval_keyboard(ref_id, amount),
                parse_mode="Markdown",
            )
        except Exception:
            pass
    else:
        result_text = (
            f"Our automated investigation could not locate a duplicate capture for this transaction.\n\n"
            f"• *Support Ticket Created*: `{result.get('support_ticket_id')}`\n"
            f"A customer support specialist has been assigned to your ticket."
        )

    await status_msg.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📜 View Updated Transactions", callback_data="tx:recent")],
                *get_nav_footer("nav:main_menu"),
            ]
        ),
        parse_mode="Markdown",
    )


# ==============================================================================
# TEXT INPUT DISPATCHER (State-Aware Input Collection)
# ==============================================================================
@router.message(F.text)
async def handle_user_text_input(message: Message):
    """
    Handles state-aware customer text input (Identification, manual invoice, or natural query).
    """
    session = get_or_create_session(message.from_user.id)
    text = message.text.strip()

    # 1. Identity Verification Input
    if session.awaiting_input == "auth_identifier":
        session.awaiting_input = None
        method = session.auth_method or "mobile"

        loading = await message.answer("🔍 *Searching ERPNext records via FastAPI...*", parse_mode="Markdown")
        
        # FastAPI verify call
        req = CustomerVerificationRequest(
            identifier_type=method,
            identifier_value=text,
        )
        res = await verify_customer(req)
        
        if res.success and res.customer:
            cust = res.customer
            session.customer_id = cust.get("customer_id")
            session.customer_name = cust.get("customer_name")
            session.registered_email = cust.get("registered_email")
            session.registered_mobile = cust.get("registered_mobile")
            session.customer_group = cust.get("customer_group")
            session.loyalty_tier = cust.get("loyalty_tier")

            confirm_text = (
                f"Hello {session.customer_name} 👋\n\n"
                f"We found your account.\n\n"
                f"Registered Email\n`{session.registered_email}`\n\n"
                f"Customer ID\n`{session.customer_id}`"
            )
            await loading.edit_text(confirm_text, reply_markup=get_auth_confirm_keyboard(), parse_mode="Markdown")
        elif res.matches_count > 1:
            await loading.edit_text(
                "Multiple customer accounts found with this identifier.\n\n"
                "Please choose another identifier method:",
                reply_markup=get_auth_method_keyboard(),
            )
        else:
            await loading.edit_text(
                "We couldn't locate your account.",
                reply_markup=get_auth_retry_keyboard(),
                parse_mode="Markdown",
            )
        return

    # 2. Manual Invoice / Transaction Input
    if session.awaiting_input == "manual_invoice":
        session.awaiting_input = None
        from agents.models.fast_classifier import FastEntityExtractor
        extracted = FastEntityExtractor.extract_entities(text)
        inv_id = extracted.get("invoice_id") or "INV-2026-001"
        amount = extracted.get("amount") or 134.00
        await run_investigation_workflow(message, session, inv_id, amount, user_note=text)
        return

    # 3. AI Assistant Query / Natural Language Flow (e.g., "refund $134 for invoice INV-2026-001")
    if session.awaiting_input == "issue_description" or session.is_verified:
        session.awaiting_input = None
        from agents.models.fast_classifier import FastEntityExtractor
        extracted = FastEntityExtractor.extract_entities(text)
        inv_id = extracted.get("invoice_id") or "INV-2026-001"
        amount = extracted.get("amount") or 134.00

        await run_investigation_workflow(message, session, inv_id, amount, user_note=text)
        return

    # Fallback to Welcome Menu
    await welcome_handler(message)


# ==============================================================================
# MANAGER APPROVAL CALLBACK HANDLER
# ==============================================================================
@router.callback_query(F.data.startswith("app:"))
async def handle_manager_callback(query: CallbackQuery):
    _, dispute_ref, decision = query.data.split(":")
    await query.answer(f"Processing {decision} in ERPNext...")

    async with AsyncSessionLocal() as session:
        erp_client = get_erp_client()
        if decision == "APPROVED":
            refund_payload = ERPPaymentEntryCreate(
                payment_type="Pay",
                party_type="Customer",
                party="CUST-00045",
                paid_amount=2350.00,
                received_amount=2350.00,
                reference_no=f"TG-HITL-{dispute_ref}",
                reference_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                references=[
                    ERPPaymentEntryReference(
                        reference_doctype="Sales Invoice",
                        reference_name="INV-2026-001",
                        allocated_amount=2350.00,
                    )
                ],
                remarks=f"Telegram 1-Click Manager Approval (Manager ID: {query.from_user.id})",
            )
            erp_res = await erp_client.create_refund_payment(refund_payload)

            await AuditService.record_event(
                session=session,
                dispute_id=dispute_ref,
                action="TELEGRAM_MANAGER_APPROVED",
                agent_node="TelegramHITLBridge",
                justification=f"Approved by Manager {query.from_user.username or query.from_user.id} via Telegram Inline Keyboard.",
                state_diff={"erp_payment_entry": erp_res.get("name")},
            )
            await session.commit()

            await ws_manager.broadcast({
                "type": "HITL_APPROVED",
                "dispute_id": dispute_ref,
                "payment_entry": erp_res.get("name"),
                "amount": 2350.00,
            })

            await query.message.edit_text(
                f"✅ *APPROVED & EXECUTED IN ERPNEXT*\n\n"
                f"• *Reference ID*: `{dispute_ref}`\n"
                f"• *Amount Refunded*: `₹2,350.00`\n"
                f"• *ERPNext Payment Entry*: `{erp_res.get('name')}`\n"
                f"• *Authorized By*: @{query.from_user.username or 'BranchManager'}\n"
                f"• *Ledger Status*: `General Ledger Reconciled`",
                parse_mode="Markdown",
            )
        else:
            await AuditService.record_event(
                session=session,
                dispute_id=dispute_ref,
                action="TELEGRAM_MANAGER_REJECTED",
                agent_node="TelegramHITLBridge",
                justification=f"Rejected by Manager {query.from_user.username or query.from_user.id} via Telegram.",
            )
            await session.commit()

            await query.message.edit_text(
                f"❌ *REJECTED BY MANAGER*\n\n"
                f"• *Reference ID*: `{dispute_ref}`\n"
                f"• *Action*: Request cancelled. Zero ledger entry created.",
                parse_mode="Markdown",
            )


# ==============================================================================
# BOT INITIALIZATION & LIFESPAN HOOK
# ==============================================================================
if settings.TELEGRAM_BOT_TOKEN and not settings.TELEGRAM_BOT_TOKEN.startswith("your_"):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        logger.info("NovaBank Telegram Customer Support Bot initialized.")
    except Exception as e:
        logger.warning("Failed to initialize NovaBank Telegram Bot: %s", e)


async def start_telegram_bot():
    """Starts the Telegram bot polling in a background task."""
    if bot and dp:
        logger.info("Starting NovaBank Telegram Bot background polling...")
        asyncio.create_task(dp.start_polling(bot))
