from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class QuestionCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    stem_en: str = Field(..., description="Question text in English")
    options_en: List[str] = Field(..., min_items=2, max_items=6, description="Answer options in English")
    stem_ru: Optional[str] = Field(None, description="Question text in Russian")
    options_ru: Optional[List[str]] = Field(None, min_items=2, max_items=6, description="Answer options in Russian")
    correct_option: int = Field(..., ge=0, description="Index of correct option (0-based)")
    tags_en: List[str] = Field(..., description="Question tags in English")
    tags_ru: Optional[List[str]] = Field(None, description="Question tags in Russian")
    difficulty_hint: Optional[float] = Field(None, ge=0, le=10, description="Difficulty hint (0-10)")

class QuestionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    id: int
    stem: str
    options: List[str]
    correct_option: int
    tags: List[str]
    difficulty_hint: Optional[float]
    created_at: datetime

class QuestionList(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    questions: List[QuestionResponse]
    total: int
    page: int
    size: int
