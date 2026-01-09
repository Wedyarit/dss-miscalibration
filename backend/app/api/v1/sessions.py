from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.crud import create_session, get_session, finish_session, create_interaction, get_item, get_user
from app.schemas.sessions import SessionCreate, SessionResponse, AnswerSubmit, AnswerResponse, SessionPurpose
from app.ml.irt_elo import update_elo_ratings, update_user_aggregates, update_item_aggregates, update_beta_binomial_difficulty
from app.db.crud import get_or_create_user_aggregate, get_or_create_item_aggregate, update_user_aggregate, update_item_aggregate
from datetime import datetime

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

    purpose_value = session.purpose.value if session.purpose else "real"
    db_session = create_session(db, session.user_id, session.mode.value, purpose_value)

    # Convert purpose string to enum if needed
    purpose_enum = None
    if db_session.purpose:
        try:
            purpose_enum = SessionPurpose(db_session.purpose)
        except ValueError:
            purpose_enum = SessionPurpose.REAL  # Default fallback

    return SessionResponse(
        id=db_session.id,
        user_id=db_session.user_id,
        mode=session.mode,
        purpose=purpose_enum,
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

    # Convert purpose string to enum if needed
    purpose_enum = None
    if db_session.purpose:
        try:
            purpose_enum = SessionPurpose(db_session.purpose)
        except ValueError:
            purpose_enum = SessionPurpose.REAL  # Default fallback

    return SessionResponse(
        id=db_session.id,
        user_id=db_session.user_id,
        mode=db_session.mode,
        purpose=purpose_enum,
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
        attempts_count=1,
        answer_changes_count=answer.answer_changes_count,
        time_to_first_choice_ms=answer.time_to_first_choice_ms,
        time_after_choice_ms=answer.time_after_choice_ms
    )

    # Update Elo ratings and aggregates
    try:
        # Get current aggregates
        user_aggregate = get_or_create_user_aggregate(db, db_session.user_id)
        item_aggregate = get_or_create_item_aggregate(db, answer.item_id)

        # Update Elo ratings for user ability (theta_user)
        new_user_ability, _ = update_elo_ratings(
            user_aggregate.elo_ability,
            item_aggregate.elo_difficulty,  # Still used for Elo calculation, but not updated for real items
            is_correct
        )

        # Update user aggregates (always update for both calibration and real)
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
                'elo_difficulty': item_aggregate.elo_difficulty,
                'bb_alpha': item_aggregate.bb_alpha if hasattr(item_aggregate, 'bb_alpha') and item_aggregate.bb_alpha else 1.0,
                'bb_beta': item_aggregate.bb_beta if hasattr(item_aggregate, 'bb_beta') and item_aggregate.bb_beta else 1.0,
                'bb_n': item_aggregate.bb_n if hasattr(item_aggregate, 'bb_n') else 0
            }
        )

        # Update Beta-Binomial difficulty ONLY for real interactions
        if db_session.purpose == "real":
            new_bb_alpha, new_bb_beta = update_beta_binomial_difficulty(
                item_updates['bb_alpha'],
                item_updates['bb_beta'],
                is_correct
            )
            item_updates['bb_alpha'] = new_bb_alpha
            item_updates['bb_beta'] = new_bb_beta
            item_updates['bb_n'] = item_updates.get('bb_n', 0) + 1
            item_updates['bb_updated_at'] = datetime.utcnow()

        # Keep Elo difficulty for backward compatibility (but don't update it for real items)
        # For calibration, we can still update Elo if needed
        if db_session.purpose == "calibration":
            _, new_item_difficulty = update_elo_ratings(
                user_aggregate.elo_ability,
                item_aggregate.elo_difficulty,
                is_correct
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
