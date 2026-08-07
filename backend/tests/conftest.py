import pytest
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.services.erpnext_mock import get_erp_client


@pytest.fixture(autouse=True)
async def setup_test_environment():
    # Force mock mode during automated pytest runs for deterministic ground truth
    original_mode = settings.ERPNEXT_MODE
    settings.ERPNEXT_MODE = "mock"
    
    await init_db()
    client = get_erp_client()
    if hasattr(client, "reset"):
        client.reset()
    yield
    settings.ERPNEXT_MODE = original_mode
