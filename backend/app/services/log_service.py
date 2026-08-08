import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.system_log import SystemLog


class SQLLoggingHandler(logging.Handler):
    """
    Python standard logging handler that asynchronously writes logs to the SQL database.
    """

    def emit(self, record: logging.LogRecord):
        # Avoid recursive logging from sqlalchemy/aiosqlite internals
        if record.name.startswith("sqlalchemy") or record.name.startswith("aiosqlite"):
            return

        try:
            log_entry = {
                "id": f"LOG-{uuid.uuid4().hex[:12].upper()}",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": record.levelname,
                "logger_name": record.name,
                "message": self.format(record),
                "module": record.module,
                "func_name": record.funcName,
                "line_no": record.lineno,
                "extra_data": getattr(record, "extra_data", None),
            }
            # Run async write in background event loop if running
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_write_log(log_entry))
            except RuntimeError:
                pass
        except Exception:
            self.handleError(record)

    async def _async_write_log(self, entry: Dict[str, Any]):
        try:
            async with AsyncSessionLocal() as session:
                log = SystemLog(
                    id=entry["id"],
                    timestamp=entry["timestamp"],
                    level=entry["level"],
                    logger_name=entry["logger_name"],
                    message=entry["message"],
                    module=entry["module"],
                    func_name=entry["func_name"],
                    line_no=entry["line_no"],
                    extra_data=entry["extra_data"],
                )
                session.add(log)
                await session.commit()
        except Exception:
            pass


async def get_system_logs_from_db(
    limit: int = 100,
    level: Optional[str] = None,
    logger_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves logs stored in SQL database."""
    async with AsyncSessionLocal() as session:
        stmt = select(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit)
        if level:
            stmt = stmt.where(SystemLog.level == level.upper())
        if logger_name:
            stmt = stmt.where(SystemLog.logger_name.ilike(f"%{logger_name}%"))
        result = await session.execute(stmt)
        logs = result.scalars().all()
        return [log.to_dict() for log in logs]


def setup_sql_logging():
    """Attaches SQLLoggingHandler to the root logger."""
    root_logger = logging.getLogger()
    sql_handler = SQLLoggingHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    sql_handler.setFormatter(formatter)
    root_logger.addHandler(sql_handler)
