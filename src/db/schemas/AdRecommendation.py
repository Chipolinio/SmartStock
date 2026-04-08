from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict, StrictInt
from datetime import datetime


class AdRecommendationBase(BaseModel):
    category: Annotated[Optional[str], Field(None)]
    recommendation_text: Annotated[str, Field(..., min_length=1)]
    priority: Annotated[int, Field(default=2, ge=1, le=3)]
    metadata_json: Annotated[Optional[str], Field(None)]

    model_config = ConfigDict(str_strip_whitespace=True)


class AdRecommendationCreate(AdRecommendationBase):
    user_id: Annotated[int, Field(..., gt=0)]
    product_id: Annotated[Optional[int], Field(None, gt=0)]
    created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]


class AdRecommendationResponse(AdRecommendationBase):
    id: Annotated[StrictInt, Field(..., ge=1)]
    user_id: Annotated[int, Field(...)]
    product_id: Annotated[Optional[int], Field(None)]
    created_at: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class AdRecommendationGenerateRequest(BaseModel):
    product_ids: Annotated[Optional[List[int]], Field(None)]
    prompt_type: Annotated[str, Field(default="full")]


class AdRecommendationsListResponse(BaseModel):
    items: Annotated[List[AdRecommendationResponse], Field(...)]
    total: Annotated[int, Field(..., ge=0)]

    model_config = ConfigDict(from_attributes=True)
