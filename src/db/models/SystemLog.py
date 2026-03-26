from sqlalchemy import String, Integer, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum

from src.db.models.Base import Base


class TaskStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class SystemLog(Base):
    __tablename__ = "system_log"

    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status"),
        nullable=False
    )
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict | None] = mapped_column(
        String,  # JSONB будет настроен через миграцию или при использовании
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
