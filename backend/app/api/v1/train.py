from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ml.train import train_model
from app.schemas.analytics import TrainRequest, TrainResponse
from app.core.security import verify_api_key

router = APIRouter()

@router.post("/", response_model=TrainResponse)
async def train_model_endpoint(
    train_request: TrainRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Train the miscalibration prediction model"""
    
    try:
        result = train_model(
            confidence_threshold=train_request.confidence_threshold,
            calibration=train_request.calibration,
            bins=train_request.bins,
            test_size=train_request.test_size
        )
        
        return TrainResponse(**result)
        
    except Exception as e:
        return TrainResponse(
            success=False,
            error=str(e)
        )
