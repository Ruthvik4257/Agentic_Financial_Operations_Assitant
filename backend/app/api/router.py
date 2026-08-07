from fastapi import APIRouter
from backend.app.api.v1.disputes import router as disputes_router
from backend.app.api.v1.approvals import router as approvals_router
from backend.app.api.v1.erp import router as erp_router
from backend.app.api.v1.metrics import router as metrics_router
from backend.app.api.v1.websocket import router as ws_router
from backend.app.api.v1.gateways import router as gateways_router
from backend.app.api.v1.policies import router as policies_router
from backend.app.api.v1.compliance import router as compliance_router
from backend.app.api.v1.settlements import router as settlements_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(disputes_router)
api_router.include_router(approvals_router)
api_router.include_router(erp_router)
api_router.include_router(metrics_router)
api_router.include_router(ws_router)
api_router.include_router(gateways_router)
api_router.include_router(policies_router)
api_router.include_router(compliance_router)
api_router.include_router(settlements_router)
