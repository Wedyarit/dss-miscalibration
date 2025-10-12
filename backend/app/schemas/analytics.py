from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class TrainRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Confidence threshold for confident errors")
    calibration: str = Field("platt", description="Calibration method: platt, isotonic, or none")
    bins: int = Field(10, ge=5, le=20, description="Number of bins for calibration metrics")
    test_size: float = Field(0.2, ge=0.1, le=0.5, description="Test set size")

class TrainResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    success: bool
    model_version: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    n_samples: Optional[int] = None
    n_features: Optional[int] = None
    model_id: Optional[int] = None
    error: Optional[str] = None

class AnalyticsOverview(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    ece: float = Field(..., description="Expected Calibration Error")
    mce: float = Field(..., description="Maximum Calibration Error")
    brier: float = Field(..., description="Brier Score")
    roc_auc: float = Field(..., description="ROC AUC")
    confident_error_rate: float = Field(..., description="Confident Error Rate")
    total_interactions: int = Field(..., description="Total interactions")
    interactions_with_confidence: int = Field(..., description="Interactions with confidence scores")
    model_version: Optional[str] = Field(None, description="Latest model version")

class ReliabilityBin(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    bin_low: float = Field(..., description="Lower bound of confidence bin")
    bin_high: float = Field(..., description="Upper bound of confidence bin")
    conf_avg: float = Field(..., description="Average confidence in bin")
    acc_avg: float = Field(..., description="Average accuracy in bin")
    count: int = Field(..., description="Number of samples in bin")

class ReliabilityResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    bins: List[ReliabilityBin]
    n_bins: int
    model_version: Optional[str] = None

class ProblematicItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    item_id: int
    stem: str
    tags: List[str]
    confident_error_rate: float
    total_interactions: int
    avg_confidence: float
    avg_accuracy: float

class ProblematicItemsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    items: List[ProblematicItem]
    total_items: int
    threshold: float = 0.7

class ExportRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    start_date: Optional[datetime] = Field(None, description="Start date for export")
    end_date: Optional[datetime] = Field(None, description="End date for export")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    session_id: Optional[int] = Field(None, description="Filter by session ID")
