import os
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from backend.app.core.config import settings

# Ensure data directory exists for SQLite
if "sqlite" in settings.DATABASE_URL:
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    Path(os.path.dirname(db_path) or "./data").mkdir(parents=True, exist_ok=True)

# Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables, run lightweight migrations, and seed initial customers."""
    # Import all models to register with Base.metadata
    from backend.app.models.customer import Customer
    from backend.app.models.sales_invoice import SalesInvoice
    from backend.app.models.payment_entry import PaymentEntry
    from backend.app.models.support_issue import SupportIssue
    from backend.app.models.dispute import Dispute
    from backend.app.models.approval import ApprovalRequest
    from backend.app.models.audit import AuditLog
    from backend.app.models.system_log import SystemLog

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "sqlite" in settings.DATABASE_URL:
            def _migrate_columns(sync_conn):
                from sqlalchemy import text
                res = sync_conn.execute(text("PRAGMA table_info(disputes)"))
                cols = {row[1] for row in res.fetchall()}
                if cols and "telegram_chat_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE disputes ADD COLUMN telegram_chat_id VARCHAR(64)"))
            await conn.run_sync(_migrate_columns)

    # Seed initial customers & invoices into SQL if empty
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            res = await session.execute(select(Customer).limit(1))
            if res.scalar_one_or_none() is None:
                # Seed core customer accounts
                customers_dict = {
                    "CUST-00045": Customer(
                        id="CUST-00045",
                        customer_name="Rahul Sharma",
                        email="rahul.sharma@gmail.com",
                        mobile="9876543210",
                        customer_group="Retail Banking",
                        territory="India",
                        credit_limit=150000.0,
                        loyalty_tier="Platinum",
                        total_invoiced=14750.0,
                    ),
                    "CUST-001": Customer(
                        id="CUST-001",
                        customer_name="Acme Corporation",
                        email="finance@acmecorp.com",
                        mobile="9876500001",
                        customer_group="Enterprise Commercial",
                        territory="United States",
                        credit_limit=50000.0,
                        loyalty_tier="Platinum",
                        total_invoiced=128450.0,
                    ),
                    "CUST-002": Customer(
                        id="CUST-002",
                        customer_name="Globex Logistics Corp",
                        email="accounts@globexcorp.com",
                        mobile="9876500002",
                        customer_group="Global Logistics",
                        territory="North America",
                        credit_limit=25000.0,
                        loyalty_tier="Gold",
                        total_invoiced=42100.0,
                    ),
                    "CUST-003": Customer(
                        id="CUST-003",
                        customer_name="Initech Software Labs",
                        email="billing@initechlabs.com",
                        mobile="9876500003",
                        customer_group="SMB Software",
                        territory="United Kingdom",
                        credit_limit=10000.0,
                        loyalty_tier="Silver",
                        total_invoiced=8500.0,
                    ),
                }

                # Generate realistic customer directory up to 180+ accounts
                first_names = ["Amit", "Priya", "Vikram", "Sneha", "Rohan", "Ananya", "Karan", "Pooja", "Arjun", "Neha", "Siddharth", "Meera", "Aditya", "Riya", "Varun"]
                last_names = ["Patel", "Verma", "Singh", "Reddy", "Mehta", "Nair", "Gupta", "Deshmukh", "Iyer", "Chopra", "Kulkarni", "Sharma", "Bhatt", "Kapoor", "Joshi"]
                for i in range(4, 200):
                    cid = f"CUST-{i:05d}"
                    if cid in customers_dict or cid == "CUST-00045":
                        continue
                    fn = first_names[i % len(first_names)]
                    ln = last_names[(i // len(first_names)) % len(last_names)]
                    c_email = f"{fn.lower()}.{ln.lower()}{i}@finops-bank.com"
                    c_mobile = f"98765{i:05d}"
                    customers_dict[cid] = Customer(
                        id=cid,
                        customer_name=f"{fn} {ln}",
                        email=c_email,
                        mobile=c_mobile,
                        customer_group="Retail Banking" if i % 2 == 0 else "Corporate Banking",
                        territory="India" if i % 3 != 0 else "United States",
                        credit_limit=50000.0 + (i * 500),
                        loyalty_tier="Platinum" if i % 5 == 0 else ("Gold" if i % 2 == 0 else "Silver"),
                        total_invoiced=2500.0 + (i * 120),
                    )

                for c in customers_dict.values():
                    session.add(c)

                # Seed invoices
                invoices_seed = [
                    SalesInvoice(
                        id="INV-2026-001",
                        customer_id="CUST-00045",
                        customer_name="Rahul Sharma",
                        posting_date="2026-08-01",
                        due_date="2026-08-31",
                        grand_total=2350.0,
                        outstanding_amount=0.0,
                        status="Paid",
                        currency="INR",
                        item_code="CLOUD-OPS-SEAT",
                        item_name="Cloud Operations Seat License",
                        qty=1.0,
                        rate=2350.0,
                    ),
                    SalesInvoice(
                        id="INV-2026-134",
                        customer_id="CUST-00045",
                        customer_name="Rahul Sharma",
                        posting_date="2026-08-02",
                        due_date="2026-09-01",
                        grand_total=134.0,
                        outstanding_amount=0.0,
                        status="Paid",
                        currency="USD",
                        item_code="API-MICRO-USAGE",
                        item_name="Cloud API Micro-Usage Billing",
                        qty=1.0,
                        rate=134.0,
                    ),
                    SalesInvoice(
                        id="INV-2026-045",
                        customer_id="CUST-00045",
                        customer_name="Rahul Sharma",
                        posting_date="2026-08-03",
                        due_date="2026-09-02",
                        grand_total=8500.0,
                        outstanding_amount=0.0,
                        status="Paid",
                        currency="INR",
                        item_code="ENTERPRISE-SUPPORT",
                        item_name="Enterprise Dedicated FinOps Support",
                        qty=1.0,
                        rate=8500.0,
                    ),
                    SalesInvoice(
                        id="INV-2026-102",
                        customer_id="CUST-002",
                        customer_name="Globex Logistics Corp",
                        posting_date="2026-08-05",
                        due_date="2026-09-05",
                        grand_total=2500.0,
                        outstanding_amount=0.0,
                        status="Paid",
                        currency="USD",
                        item_code="LOGISTICS-API-BANDWIDTH",
                        item_name="Logistics API High-Throughput Tier",
                        qty=1.0,
                        rate=2500.0,
                    ),
                    SalesInvoice(
                        id="INV-2026-999",
                        customer_id="CUST-003",
                        customer_name="Initech Software Labs",
                        posting_date="2026-08-07",
                        due_date="2026-08-21",
                        grand_total=45.0,
                        outstanding_amount=0.0,
                        status="Paid",
                        currency="USD",
                        item_code="SaaS-STARTER",
                        item_name="SaaS Starter Micro-Tier",
                        qty=1.0,
                        rate=45.0,
                    ),
                ]
                for inv in invoices_seed:
                    session.add(inv)

                # Seed initial payment entries (including duplicate captures for INV-2026-001)
                payments_seed = [
                    PaymentEntry(
                        id="PE-2026001A",
                        payment_type="Receive",
                        party_type="Customer",
                        party_id="CUST-00045",
                        invoice_id="INV-2026-001",
                        paid_amount=2350.0,
                        received_amount=2350.0,
                        status="Submitted",
                        reference_no="TX-PAY-INV-2026-001",
                        posting_date="2026-08-01",
                        remarks="Credit Card Settle - Gateway Capture (2350.00 INR)",
                    ),
                    PaymentEntry(
                        id="PE-2026001B-DUP",
                        payment_type="Receive",
                        party_type="Customer",
                        party_id="CUST-00045",
                        invoice_id="INV-2026-001",
                        paid_amount=2350.0,
                        received_amount=2350.0,
                        status="Submitted",
                        reference_no="TX-PAY-INV-2026-001-DUP",
                        posting_date="2026-08-01",
                        remarks="Duplicate gateway capture anomaly (2350.00 INR)",
                    ),
                ]
                for pe in payments_seed:
                    session.add(pe)

                await session.commit()
    except Exception as e:
        import logging
        logging.getLogger("FinOpsDB").warning("Initial seed already present or completed: %s", e)


