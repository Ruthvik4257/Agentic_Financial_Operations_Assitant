import pytest
from backend.app.services.erpnext_mock import get_erp_client, EmbeddedERPNextEngine
from backend.app.schemas.erp import ERPPaymentEntryCreate, ERPPaymentEntryReference


@pytest.mark.asyncio
async def test_erpnext_get_invoice():
    client = get_erp_client()
    invoice = await client.get_invoice("INV-2026-001")
    assert invoice is not None
    assert invoice.get("customer") is not None or invoice.get("customer_id") is not None
    assert invoice.get("grand_total", 0.0) > 0.0
    assert invoice.get("status") in ["Paid", "Partly Paid", "Refunded"]


@pytest.mark.asyncio
async def test_erpnext_duplicate_payment_detection():
    client = get_erp_client()
    payments = await client.get_payment_entries_for_invoice("INV-2026-001")
    assert len(payments) >= 2  # Demonstrates duplicate billing anomaly
    total_paid = sum(p["paid_amount"] for p in payments)
    assert total_paid > 0.0



@pytest.mark.asyncio
async def test_erpnext_create_refund():
    client = get_erp_client()
    refund_payload = ERPPaymentEntryCreate(
        payment_type="Pay",
        party_type="Customer",
        party="CUST-00045",
        paid_amount=2350.00,
        received_amount=2350.00,
        reference_no="DISP-TEST-001",
        reference_date="2026-08-08",
        paid_from="1110 - Bank Account - TC",
        paid_to="2110 - Debtors - TC",
        references=[
            ERPPaymentEntryReference(
                reference_doctype="Sales Invoice",
                reference_name="INV-2026-001",
                allocated_amount=2350.00,
            )
        ],
        remarks="Test AI automated refund entry",
    )
    result = await client.create_refund_payment(refund_payload)
    assert result["payment_type"] == "Pay"
    assert result["paid_amount"] == 2350.00
    assert result["name"].startswith("PE-REF-")

