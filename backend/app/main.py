from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.router import api_router
from backend.app.api.v1.websocket import router as ws_router
from backend.app.services.telegram_service import start_telegram_bot
from backend.app.services.erpnext_mock import get_erp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and Telegram Bot
    await init_db()
    await start_telegram_bot()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Agentic AI Financial Operations Assistant for ERPNext",
    lifespan=lifespan,
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API & WebSocket Routers at both root and /api/v1
app.include_router(ws_router)
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check():
    erp_client = get_erp_client()
    invoices = await erp_client.list_all_invoices(limit=1)
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "erpnext": {
            "mode": settings.ERPNEXT_MODE,
            "connected": True,
            "invoices_available": len(invoices),
        },
        "agents": {
            "status": "ready",
            "gemini_model": settings.GEMINI_MODEL,
        },
        "telegram": {
            "configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "mode": settings.TELEGRAM_MODE,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
