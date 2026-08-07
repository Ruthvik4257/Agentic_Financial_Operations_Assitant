import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db


@pytest.mark.asyncio
async def test_health_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["erpnext"]["connected"] is True


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_disputes" in data
    assert "auto_resolved_pct" in data


@pytest.mark.asyncio
async def test_erp_mirror_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_inv = await ac.get("/api/v1/erp/invoices")
        res_pay = await ac.get("/api/v1/erp/payments")
    assert res_inv.status_code == 200
    assert len(res_inv.json()) >= 3
    assert res_pay.status_code == 200
    assert len(res_pay.json()) >= 3
