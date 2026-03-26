from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class TaskStatusEnum(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class SystemLogCreate(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=255, description="Название задачи")
    status: TaskStatusEnum = Field(..., description="Статус выполнения")
    processed_count: int = Field(default=0, ge=0, description="Количество обработанных записей")
    payload: Optional[dict[str, Any]] = Field(default=None, description="Дополнительные данные (traceback, метаданные)")

    model_config = ConfigDict(str_strip_whitespace=True)


class SystemLogResponse(SystemLogCreate):
    id: int = Field(..., ge=1, description="Внутренний ID записи")
    created_at: datetime = Field(..., description="Время создания записи")

    model_config = ConfigDict(from_attributes=True)


class TaskAcceptedResponse(BaseModel):
    """Ответ для фоновых задач (202 Accepted)."""
    status: str = Field(default="accepted", description="Статус принятия задачи")
    message: str = Field(..., description="Сообщение о запущенной задаче")

    model_config = ConfigDict(from_attributes=True)
