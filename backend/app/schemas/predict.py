from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PredictionRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    item_id: int = Field(..., description="Item ID")
    chosen_option: int = Field(..., ge=0, description="Chosen option index")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    attempts_count: int = Field(1, ge=1, description="Number of attempts")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class PredictionResponse(BaseModel):
    risk: float = Field(..., ge=0.0, le=1.0, description="Risk of confident error")
    recommendation: str = Field(..., description="Recommendation: review_answer or proceed")
    model_version: Optional[str] = Field(None, description="Model version used")
    features_used: Optional[int] = Field(None, description="Number of features used")
    error: Optional[str] = Field(None, description="Error message if any")

class BatchPredictionRequest(BaseModel):
    interactions: List[PredictionRequest] = Field(..., max_items=100, description="List of interactions to predict")

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    model_version: Optional[str]
    total_processed: int
