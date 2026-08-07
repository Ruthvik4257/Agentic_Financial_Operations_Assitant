import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db


@pytest.mark.asyncio
async def test_stripe_webhook_ingestion():
    await init_db()
    payload = {
        "id": "dp_test_12345",
        "object": "dispute",
        "amount": 150.0,
        "currency": "usd",
        "charge": "ch_test_998811",
        "invoice_id": "INV-2026-001",
        "reason": "duplicate",
        "status": "needs_response",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/gateways/stripe/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["received"] is True
    assert data["status"] in ["EXECUTED", "AWAITING_APPROVAL"]


@pytest.mark.asyncio
async def test_policy_get_and_update():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Get active policy
        get_res = await ac.get("/api/v1/policies")
        assert get_res.status_code == 200
        policy_data = get_res.json()
        assert "max_auto_refund_limit" in policy_data

        # Update policy
        update_payload = {
            "max_auto_refund_limit": 250.00,
            "max_fraud_risk_threshold": 0.35,
            "max_daily_refund_cap": 8000.00,
            "require_2fa_above": 1500.00,
            "auto_block_suspicious_accounts": True,
        }
        put_res = await ac.put("/api/v1/policies", json=update_payload)
        assert put_res.status_code == 200
        assert put_res.json()["max_auto_refund_limit"] == 250.00


@pytest.mark.asyncio
async def test_compliance_certificate_generation():
    # Ingest a test dispute first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sim_res = await ac.post("/api/v1/disputes/simulate", json={
            "customer_id": "CUST-001",
            "invoice_id": "INV-2026-001",
            "amount": 150.00,
            "reason": "Double charged for cloud seat",
            "currency": "USD",
        })
        dispute_id = sim_res.json()["id"]

        cert_res = await ac.get(f"/api/v1/compliance/certificate/{dispute_id}")
        assert cert_res.status_code == 200
        cert = cert_res.json()
        assert cert["chain_integrity_verified"] is True
        assert "merkle_root" in cert
        assert len(cert["merkle_root"]) == 64
