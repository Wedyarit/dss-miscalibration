from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class PredictionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: int = Field(..., description="User ID")
    item_id: int = Field(..., description="Item ID")
    chosen_option: int = Field(..., ge=0, description="Chosen option index")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    attempts_count: int = Field(1, ge=1, description="Number of attempts")
    timestamp: Optional[datetime] = Field(default=datetime.now(tz=timezone.utc))


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    intervention: Dict[str, Any] = Field(
        ...,
        description="Nudging payload with risk, reason_code, message_ru and show_intervention",
    )
    model_version: Optional[str] = Field(None, description="Model version used")
    features_used: Optional[int] = Field(None, description="Number of features used")
    error: Optional[str] = Field(None, description="Error message if any")


class BatchPredictionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    interactions: List[PredictionRequest] = Field(..., description="List of interactions to predict")


class BatchPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predictions: List[PredictionResponse]
    model_version: Optional[str]
    total_processed: int
