import pytest
from backend.app.core.database import init_db
from backend.app.services.erpnext_mock import get_erp_client


@pytest.fixture(autouse=True)
async def setup_test_environment():
    await init_db()
    client = get_erp_client()
    if hasattr(client, "reset"):
        client.reset()
    yield
