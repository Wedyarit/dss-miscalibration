from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.crud import create_session, get_session, finish_session, create_interaction, get_interactions_by_session, get_item, get_user
from app.schemas.sessions import SessionCreate, SessionResponse, AnswerSubmit, AnswerResponse
from app.ml.irt_elo import update_elo_ratings, update_user_aggregates, update_item_aggregates
from app.db.crud import get_or_create_user_aggregate, get_or_create_item_aggregate, update_user_aggregate, update_item_aggregate
from typing import Optional

router = APIRouter()

@router.post("/", response_model=SessionResponse)
async def create_session_endpoint(
    session: SessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new test session"""
    # Verify user exists
    user = get_user(db, session.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_session = create_session(db, session.user_id, session.mode.value)
    
    return SessionResponse(
        id=db_session.id,
        user_id=db_session.user_id,
        mode=session.mode,
        created_at=db_session.created_at,
        finished_at=db_session.finished_at
    )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get session details"""
    db_session = get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=db_session.id,
        user_id=db_session.user_id,
        mode=db_session.mode,
        created_at=db_session.created_at,
        finished_at=db_session.finished_at
    )

@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: int,
    answer: AnswerSubmit,
    language: str = Query("en", description="Language preference (en/ru)"),
    db: Session = Depends(get_db)
):
    """Submit an answer for a question"""
    # Verify session exists
    db_session = get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify item exists
    db_item = get_item(db, answer.item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if confidence is required for self_confidence mode
    if db_session.mode == "self_confidence" and answer.confidence is None:
        raise HTTPException(status_code=400, detail="Confidence is required in self_confidence mode")
    
    # Determine if answer is correct
    is_correct = answer.chosen_option == db_item.correct_option
    
    # Create interaction record
    db_interaction = create_interaction(
        db=db,
        session_id=session_id,
        user_id=db_session.user_id,
        item_id=answer.item_id,
        chosen_option=answer.chosen_option,
        is_correct=is_correct,
        confidence=answer.confidence,
        response_time_ms=answer.response_time_ms,
        attempts_count=1
    )
    
    # Update Elo ratings and aggregates
    try:
        # Get current aggregates
        user_aggregate = get_or_create_user_aggregate(db, db_session.user_id)
        item_aggregate = get_or_create_item_aggregate(db, answer.item_id)
        
        # Update Elo ratings
        new_user_ability, new_item_difficulty = update_elo_ratings(
            user_aggregate.elo_ability,
            item_aggregate.elo_difficulty,
            is_correct
        )
        
        # Update user aggregates
        user_updates = update_user_aggregates(
            db_session.user_id,
            is_correct,
            answer.confidence,
            answer.response_time_ms,
            {
                'ema_accuracy': user_aggregate.ema_accuracy,
                'ema_confidence': user_aggregate.ema_confidence,
                'ema_conf_gap': user_aggregate.ema_conf_gap,
                'avg_time_ms': user_aggregate.avg_time_ms,
                'elo_ability': user_aggregate.elo_ability
            }
        )
        user_updates['elo_ability'] = new_user_ability
        update_user_aggregate(db, db_session.user_id, **user_updates)
        
        # Update item aggregates
        item_updates = update_item_aggregates(
            answer.item_id,
            is_correct,
            answer.confidence,
            answer.response_time_ms,
            {
                'avg_accuracy': item_aggregate.avg_accuracy,
                'avg_confidence': item_aggregate.avg_confidence,
                'avg_conf_gap': item_aggregate.avg_conf_gap,
                'avg_time_ms': item_aggregate.avg_time_ms,
                'elo_difficulty': item_aggregate.elo_difficulty
            }
        )
        item_updates['elo_difficulty'] = new_item_difficulty
        update_item_aggregate(db, answer.item_id, **item_updates)
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error updating aggregates: {e}")
    
    # Generate feedback
    if is_correct:
        if language == 'ru':
            feedback = "Правильно! Отлично."
        else:
            feedback = "Correct! Well done."
    else:
        if language == 'ru':
            feedback = f"Неправильно. Правильный ответ - вариант {db_item.correct_option + 1}."
        else:
            feedback = f"Incorrect. The correct answer was option {db_item.correct_option + 1}."
    
    return AnswerResponse(
        is_correct=is_correct,
        correct_option=db_item.correct_option,
        feedback=feedback,
        session_id=session_id
    )

@router.post("/{session_id}/finish")
async def finish_session_endpoint(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Mark session as finished"""
    db_session = get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    finish_session(db, session_id)
    return {"message": "Session finished successfully"}
