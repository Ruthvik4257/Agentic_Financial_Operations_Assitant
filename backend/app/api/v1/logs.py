from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
from backend.app.services.log_service import get_system_logs_from_db
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.system_log import SystemLog
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["System & Audit Logs"])


class LogCreatePayload(BaseModel):
    level: str = "INFO"
    logger_name: str = "custom.logger"
    message: str
    module: Optional[str] = None
    func_name: Optional[str] = None
    line_no: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[Dict[str, Any]])
async def list_system_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    level: Optional[str] = Query(default=None, description="Filter by level: INFO, WARNING, ERROR, DEBUG"),
    logger_name: Optional[str] = Query(default=None, description="Filter by logger name"),
):
    """
    Fetch application, agent runtime, and execution traces directly from the SQL database (system_logs table).
    """
    logs = await get_system_logs_from_db(limit=limit, level=level, logger_name=logger_name)
    return logs


@router.post("", status_code=201)
async def create_log_entry(payload: LogCreatePayload):
    """
    Manually insert a log entry into the SQL database.
    """
    log_id = f"LOG-{uuid.uuid4().hex[:12].upper()}"
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    async with AsyncSessionLocal() as session:
        log = SystemLog(
            id=log_id,
            timestamp=timestamp_str,
            level=payload.level.upper(),
            logger_name=payload.logger_name,
            message=payload.message,
            module=payload.module,
            func_name=payload.func_name,
            line_no=payload.line_no,
            extra_data=payload.extra_data,
        )
        session.add(log)
        await session.commit()
        return log.to_dict()
