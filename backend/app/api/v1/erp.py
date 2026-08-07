from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.services.erpnext_mock import get_erp_client

router = APIRouter(prefix="/erp", tags=["ERPNext"])


@router.get("/invoices", response_model=List[Dict[str, Any]])
async def get_all_invoices():
    client = get_erp_client()
    return await client.list_all_invoices()


@router.get("/payments", response_model=List[Dict[str, Any]])
async def get_all_payments():
    client = get_erp_client()
    return await client.list_all_payments()
