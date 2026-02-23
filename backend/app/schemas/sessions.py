from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from app.schemas.questions import QuestionResponse

class SessionMode(str, Enum):
    STANDARD = "standard"
    SELF_CONFIDENCE = "self_confidence"

class SessionPurpose(str, Enum):
    CALIBRATION = "calibration"
    REAL = "real"

class SessionCreate(BaseModel):
    user_id: int = Field(..., description="User ID")
    mode: SessionMode = Field(SessionMode.STANDARD, description="Session mode")
    purpose: Optional[SessionPurpose] = Field(SessionPurpose.REAL, description="Session purpose: calibration or real")

class SessionResponse(BaseModel):
    id: int
    user_id: int
    mode: SessionMode
    purpose: Optional[SessionPurpose] = None
    created_at: datetime
    finished_at: Optional[datetime]

class AnswerSubmit(BaseModel):
    item_id: int = Field(..., description="Question ID")
    chosen_option: int = Field(..., ge=0, description="Chosen option index (0-based)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level (0.0-1.0)")
    initial_chosen_option: Optional[str] = Field(
        None, description="Initial chosen option before intervention"
    )
    initial_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Initial confidence before intervention"
    )
    reconsidered: bool = Field(False, description="Whether answer was reconsidered after intervention")
    time_to_reconsider_ms: Optional[int] = Field(
        None, ge=0, description="Time spent in reconsideration loop"
    )
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    answer_changes_count: Optional[int] = Field(None, ge=0, description="Number of times user changed their answer")
    time_to_first_choice_ms: Optional[int] = Field(None, ge=0, description="Time from question start to first option selection")
    time_after_choice_ms: Optional[int] = Field(None, ge=0, description="Time from first choice to submission")

class AnswerResponse(BaseModel):
    is_correct: bool
    correct_option: int
    feedback: str
    session_id: int


class SimulatedUserRequest(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=120, description="Student display name")


class SimulatedUserResponse(BaseModel):
    user_id: int
    student_name: str
    is_new: bool


class ConfidencePolicyRequest(BaseModel):
    item_id: int = Field(..., description="Question ID")


class ConfidencePolicyResponse(BaseModel):
    should_request_confidence: bool
    confidence_sampling_rate: float
    mode: SessionMode


class NextQuestionResponse(BaseModel):
    question: QuestionResponse
    require_confidence: bool
