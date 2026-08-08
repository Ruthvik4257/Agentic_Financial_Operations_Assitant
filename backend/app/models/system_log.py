from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Text, JSON, Integer
from backend.app.core.database import Base


class SystemLog(Base):
    """
    SQL-persisted system and agent runtime logs.
    Captures all application logs, agent execution traces, and API events directly into SQL database.
    """
    __tablename__ = "system_logs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(String(64), nullable=False, index=True)
    level = Column(String(16), nullable=False, index=True) # INFO, WARNING, ERROR, DEBUG
    logger_name = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(64), nullable=True)
    func_name = Column(String(64), nullable=True)
    line_no = Column(Integer, nullable=True)
    extra_data = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level,
            "logger_name": self.logger_name,
            "message": self.message,
            "module": self.module,
            "func_name": self.func_name,
            "line_no": self.line_no,
            "extra_data": self.extra_data,
        }
