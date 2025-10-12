from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ml.inference import predict_confident_error, predict_batch
from app.schemas.predict import PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=PredictionResponse)
async def predict_single(
    prediction: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Predict confident error risk for a single interaction"""
    
    interaction_data = {
        'confidence': prediction.confidence,
        'response_time_ms': prediction.response_time_ms,
        'attempts_count': prediction.attempts_count,
        'timestamp': prediction.timestamp
    }
    
    result = predict_confident_error(
        prediction.user_id,
        prediction.item_id,
        interaction_data
    )
    
    return PredictionResponse(**result)

@router.post("/batch", response_model=BatchPredictionResponse)
async def predict_batch_endpoint(
    batch_request: BatchPredictionRequest,
    db: Session = Depends(get_db)
):
    """Predict confident error risk for multiple interactions"""
    
    interactions = []
    for pred in batch_request.interactions:
        interactions.append({
            'user_id': pred.user_id,
            'item_id': pred.item_id,
            'confidence': pred.confidence,
            'response_time_ms': pred.response_time_ms,
            'attempts_count': pred.attempts_count,
            'timestamp': pred.timestamp
        })
    
    results = predict_batch(interactions)
    
    return BatchPredictionResponse(
        predictions=[PredictionResponse(**result) for result in results],
        model_version=results[0].get('model_version') if results else None,
        total_processed=len(results)
    )
