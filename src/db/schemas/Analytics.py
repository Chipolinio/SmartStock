from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict

class AnalyticsMetrics(BaseModel):
    abc: Annotated[str, Field(..., pattern="^[A-C]$")]
    xyz: Annotated[str, Field(..., pattern="^[X-Z]$")]
    segment: Annotated[str, Field(..., description="Комбинация ABC-XYZ")]
    score: Annotated[float, Field(..., ge=0, le=1)]
    revenue: Annotated[float, Field(..., description="Выручка за период")]

class ProductAnalyticsResponse(BaseModel):
    product_id: Annotated[int, Field(..., gt=0)]
    subject: Annotated[Optional[str], Field(None)]
    metrics: Annotated[AnalyticsMetrics, Field(...)]
    advice: Annotated[str, Field(...)]

    model_config = ConfigDict(from_attributes=True)