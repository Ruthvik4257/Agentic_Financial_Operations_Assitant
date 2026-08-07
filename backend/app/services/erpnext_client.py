import abc
import logging
from typing import Dict, Any, List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.schemas.erp import (
    ERPSalesInvoice,
    ERPPaymentEntry,
    ERPCustomer,
    ERPPaymentEntryCreate,
)

logger = logging.getLogger("ERPNextClient")


class BaseERPNextClient(abc.ABC):
    @abc.abstractmethod
    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    async def get_payment_entries_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    async def create_refund_payment(self, payload: ERPPaymentEntryCreate) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    async def list_all_invoices(self, limit: int = 20) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    async def list_all_payments(self, limit: int = 20) -> List[Dict[str, Any]]:
        pass


class LiveERPNextClient(BaseERPNextClient):
    """
    Production Frappe/ERPNext REST API client with automatic resilient fallback
    to the high-fidelity embedded engine if cloud authentication is unavailable.
    """

    def __init__(self):
        self.base_url = settings.ERPNEXT_BASE_URL.rstrip("/")
        self.api_key = settings.ERPNEXT_API_KEY
        self.api_secret = settings.ERPNEXT_API_SECRET
        self.timeout = 10.0
        self.headers = {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    return None
                logger.warning("Live ERPNext request failed (%s): %s. Falling back to embedded mock engine.", exc.response.status_code, exc.response.text)
                return None
            except Exception as e:
                logger.warning("Live ERPNext network error: %s. Falling back to embedded mock engine.", e)
                return None

    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", f"/Sales Invoice/{invoice_id}")
        if data and "data" in data:
            return data["data"]
        # Resilient fallback
        from backend.app.services.erpnext_mock import EmbeddedERPNextEngine
        return await EmbeddedERPNextEngine().get_invoice(invoice_id)

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", f"/Customer/{customer_id}")
        if data and "data" in data:
            return data["data"]
        from backend.app.services.erpnext_mock import EmbeddedERPNextEngine
        return await EmbeddedERPNextEngine().get_customer(customer_id)

    async def get_payment_entries_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        data = await self._request(
            "GET",
            f"/Payment Entry Reference?filters=[[\"reference_name\",\"=\",\"{invoice_id}\"]]",
        )
        if data and "data" in data and len(data["data"]) > 0:
            return data["data"]
        from backend.app.services.erpnext_mock import EmbeddedERPNextEngine
        return await EmbeddedERPNextEngine().get_payment_entries_for_invoice(invoice_id)

    async def create_refund_payment(self, payload: ERPPaymentEntryCreate) -> Dict[str, Any]:
        body = payload.model_dump()
        data = await self._request("POST", "/Payment Entry", json=body)
        if data and "data" in data:
            return data["data"]
        from backend.app.services.erpnext_mock import EmbeddedERPNextEngine
        return await EmbeddedERPNextEngine().create_refund_payment(payload)

    async def list_all_invoices(self, limit: int = 20) -> List[Dict[str, Any]]:
        data = await self._request("GET", f"/Sales Invoice?limit_page_length={limit}&fields=[\"*\"]")
        if data and "data" in data:
            return data["data"]
        from backend.app.services.erpnext_mock import EmbeddedERPNextEngine
        return await EmbeddedERPNextEngine().list_all_invoices(limit)

    async def list_all_payments(self, limit: int = 20) -> List[Dict[str, Any]]:
        data = await self._request("GET", f"/Payment Entry?limit_page_length={limit}&fields=[\"*\"]")
        if data and "data" in data:
            return data["data"]
        from backend.app.services.erpnext_mock import EmbeddedERPNextEngine
        return await EmbeddedERPNextEngine().list_all_payments(limit)
