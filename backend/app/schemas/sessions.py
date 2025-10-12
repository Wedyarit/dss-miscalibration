from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class SessionMode(str, Enum):
    STANDARD = "standard"
    SELF_CONFIDENCE = "self_confidence"

class SessionCreate(BaseModel):
    user_id: int = Field(..., description="User ID")
    mode: SessionMode = Field(..., description="Session mode")

class SessionResponse(BaseModel):
    id: int
    user_id: int
    mode: SessionMode
    created_at: datetime
    finished_at: Optional[datetime]

class AnswerSubmit(BaseModel):
    item_id: int = Field(..., description="Question ID")
    chosen_option: int = Field(..., ge=0, description="Chosen option index (0-based)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level (0.0-1.0)")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")

class AnswerResponse(BaseModel):
    is_correct: bool
    correct_option: int
    feedback: str
    session_id: int
