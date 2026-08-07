import abc
from typing import Dict, Any, List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.schemas.erp import (
    ERPSalesInvoice,
    ERPPaymentEntry,
    ERPPaymentEntryCreate,
    ERPCustomer,
)


class BaseERPNextClient(abc.ABC):
    """Abstract Base Class for ERPNext System of Record Integration."""

    @abc.abstractmethod
    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Sales Invoice by name/ID."""
        pass

    @abc.abstractmethod
    async def list_invoices_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """List all invoices for a customer."""
        pass

    @abc.abstractmethod
    async def get_payment_entries_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        """Fetch Payment Entries linked to an invoice."""
        pass

    @abc.abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Customer profile and credit terms."""
        pass

    @abc.abstractmethod
    async def create_refund_payment(self, payload: ERPPaymentEntryCreate) -> Dict[str, Any]:
        """Post a negative Payment Entry (Refund) in ERPNext."""
        pass

    @abc.abstractmethod
    async def list_all_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all invoices in the system."""
        pass

    @abc.abstractmethod
    async def list_all_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all payment entries in the system."""
        pass


class LiveERPNextClient(BaseERPNextClient):
    """
    Production-grade HTTP client communicating with Frappe/ERPNext via standard REST API.
    Zero modifications to ERPNext core.
    """

    def __init__(self):
        self.base_url = settings.ERPNEXT_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"token {settings.ERPNEXT_API_KEY}:{settings.ERPNEXT_API_SECRET}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    return None
                raise RuntimeError(f"ERPNext API Error ({exc.response.status_code}): {exc.response.text}") from exc
            except httpx.RequestError as exc:
                raise ConnectionError(f"ERPNext connection failed at {url}: {str(exc)}") from exc

    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", f"/Sales Invoice/{invoice_id}")
        return data.get("data") if data else None

    async def list_invoices_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        filters = f'[["customer","=","{customer_id}"]]'
        data = await self._request("GET", f"/Sales Invoice?filters={filters}&fields=[\"*\"]")
        return data.get("data", []) if data else []

    async def get_payment_entries_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        # In Frappe, Payment Entry References link to invoices
        filters = f'[["reference_name","=","{invoice_id}"]]'
        data = await self._request("GET", f"/Payment Entry Reference?filters={filters}&fields=[\"*\"]")
        ref_data = data.get("data", []) if data else []
        payment_names = [ref.get("parent") for ref in ref_data if ref.get("parent")]
        
        payments = []
        for p_name in set(payment_names):
            p_data = await self._request("GET", f"/Payment Entry/{p_name}")
            if p_data and "data" in p_data:
                payments.append(p_data["data"])
        return payments

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", f"/Customer/{customer_id}")
        return data.get("data") if data else None

    async def create_refund_payment(self, payload: ERPPaymentEntryCreate) -> Dict[str, Any]:
        data = await self._request("POST", "/Payment Entry", json=payload.model_dump())
        return data.get("data") if data else {}

    async def list_all_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        data = await self._request("GET", f"/Sales Invoice?limit_page_length={limit}&fields=[\"*\"]")
        return data.get("data", []) if data else []

    async def list_all_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        data = await self._request("GET", f"/Payment Entry?limit_page_length={limit}&fields=[\"*\"]")
        return data.get("data", []) if data else []
