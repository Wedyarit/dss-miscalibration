import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.crud import (
    create_session,
    get_session,
    finish_session,
    create_interaction,
    get_item,
    get_user,
    create_user,
    get_or_create_student_by_name,
    get_or_create_user_aggregate,
    get_or_create_item_aggregate,
    get_random_item,
    get_localized_item,
)
from app.db.crud import update_user_aggregate, update_item_aggregate
from app.db.models import User
from app.db.session import get_db
from app.ml.irt_elo import update_elo_ratings, update_user_aggregates, update_item_aggregates, \
    update_beta_binomial_difficulty
from app.schemas.questions import QuestionResponse
from app.schemas.sessions import (
    SessionCreate,
    SessionResponse,
    AnswerSubmit,
    AnswerResponse,
    SessionPurpose,
    SimulatedUserRequest,
    SimulatedUserResponse,
    ConfidencePolicyRequest,
    ConfidencePolicyResponse,
    NextQuestionResponse,
)

router = APIRouter()

CALIBRATION_QUESTIONS_COUNT = 5


def _stable_bucket(session_id: int, user_id: int, item_id: int) -> float:
    digest = hashlib.md5(f"{session_id}:{user_id}:{item_id}".encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 1000) / 1000.0


def _resolve_require_confidence(
        session_id: int,
        user_id: int,
        item_id: int,
        answered_count: int,
        ema_conf_gap: float,
        ema_accuracy: float,
        item_error_rate: float,
        item_difficulty: float,
) -> bool:
    if answered_count < CALIBRATION_QUESTIONS_COUNT:
        return True

    # Keep asking confidence for difficult topics even after initial calibration.
    if item_difficulty >= 7.0:
        return True

    # Otherwise sample confidence requests at 30%.
    sampling_rate = 0.3
    return _stable_bucket(session_id, user_id, item_id) <= sampling_rate


@router.post("/", response_model=SessionResponse)
async def create_session_endpoint(
        session: SessionCreate,
        db: Session = Depends(get_db)
):
    """Create a new test session"""
    # Verify user exists
    user = get_user(db, session.user_id)
    if not user:
        # For UX simulation, auto-create unknown users instead of failing.
        user = create_user(db, role="student")

    purpose_value = session.purpose.value if session.purpose else "real"
    db_session = create_session(db, user.id, session.mode.value, purpose_value)

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


@router.post("/simulate-user", response_model=SimulatedUserResponse)
async def resolve_simulated_user(
        payload: SimulatedUserRequest,
        db: Session = Depends(get_db)
):
    normalized = payload.student_name.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Student name is required")
    try:
        existed = (
            db.query(User)
            .filter(User.role == "student")
            .filter(User.display_name.isnot(None))
            .filter(User.display_name.ilike(normalized))
            .first()
        )
        existing = get_or_create_student_by_name(db, normalized)
    except OperationalError:
        # Backward-compatible fallback for old DBs before additive migration is applied.
        fallback = create_user(db, role="student")
        return SimulatedUserResponse(
            user_id=fallback.id,
            student_name=normalized,
            is_new=True
        )

    return SimulatedUserResponse(
        user_id=existing.id,
        student_name=existing.display_name or normalized,
        is_new=existed is None
    )


@router.get("/{session_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question_with_policy(
        session_id: int,
        language: str = Query("en", description="Language preference (en/ru)"),
        db: Session = Depends(get_db),
):
    db_session = get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    answered_interactions = [
        interaction
        for interaction in db_session.interactions
    ]
    answered_item_ids = [interaction.item_id for interaction in answered_interactions]

    db_question = get_random_item(db, exclude_ids=answered_item_ids, language=language)
    if not db_question:
        raise HTTPException(status_code=404, detail="No questions available")

    user_aggregate = get_or_create_user_aggregate(db, db_session.user_id)
    item_aggregate = get_or_create_item_aggregate(db, db_question.id)

    ema_accuracy = float(user_aggregate.ema_accuracy or 0.0)
    ema_conf_gap = float(user_aggregate.ema_conf_gap or 0.0)
    item_error_rate = 1.0 - float(item_aggregate.avg_accuracy or 0.0)
    item_difficulty = float(db_question.difficulty_hint or 5.0)

    require_confidence = _resolve_require_confidence(
        session_id=db_session.id,
        user_id=db_session.user_id,
        item_id=db_question.id,
        answered_count=len(answered_interactions),
        ema_conf_gap=ema_conf_gap,
        ema_accuracy=ema_accuracy,
        item_error_rate=item_error_rate,
        item_difficulty=item_difficulty,
    )

    localized_question = get_localized_item(db_question, language)
    question = QuestionResponse(
        id=localized_question["id"],
        stem=localized_question["stem"],
        options=localized_question["options"],
        correct_option=localized_question["correct_option"],
        tags=localized_question["tags"],
        difficulty_hint=localized_question["difficulty_hint"],
        created_at=localized_question["created_at"],
    )

    return NextQuestionResponse(
        question=question,
        require_confidence=require_confidence,
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

    answered_count = len(db_session.interactions)
    user_aggregate = get_or_create_user_aggregate(db, db_session.user_id)
    item_aggregate = get_or_create_item_aggregate(db, answer.item_id)
    item_difficulty = float(db_item.difficulty_hint or 5.0)
    require_confidence = _resolve_require_confidence(
        session_id=db_session.id,
        user_id=db_session.user_id,
        item_id=answer.item_id,
        answered_count=answered_count,
        ema_conf_gap=float(user_aggregate.ema_conf_gap or 0.0),
        ema_accuracy=float(user_aggregate.ema_accuracy or 0.0),
        item_error_rate=1.0 - float(item_aggregate.avg_accuracy or 0.0),
        item_difficulty=item_difficulty,
    )
    effective_confidence_for_validation = (
        answer.initial_confidence if answer.initial_confidence is not None else answer.confidence
    )
    if require_confidence and effective_confidence_for_validation is None:
        raise HTTPException(status_code=400, detail="Confidence is required for this question")

    # Determine if answer is correct
    is_correct = answer.chosen_option == db_item.correct_option
    has_initial = answer.initial_chosen_option is not None
    initial_chosen_option_int = None
    if answer.initial_chosen_option is not None:
        try:
            initial_chosen_option_int = int(answer.initial_chosen_option)
        except (TypeError, ValueError):
            initial_chosen_option_int = None
    initial_is_correct = (
        initial_chosen_option_int == db_item.correct_option
        if initial_chosen_option_int is not None
        else is_correct
    )
    confidence_for_aggregates = (
        answer.initial_confidence if answer.initial_confidence is not None else answer.confidence
    )
    is_correct_for_aggregates = initial_is_correct if has_initial else is_correct

    # Create interaction record
    db_interaction = create_interaction(
        db=db,
        session_id=session_id,
        user_id=db_session.user_id,
        item_id=answer.item_id,
        chosen_option=answer.chosen_option,
        is_correct=is_correct,
        confidence=answer.confidence,
        initial_chosen_option=answer.initial_chosen_option,
        initial_confidence=answer.initial_confidence,
        reconsidered=answer.reconsidered,
        time_to_reconsider_ms=answer.time_to_reconsider_ms,
        response_time_ms=answer.response_time_ms,
        attempts_count=1,
        answer_changes_count=answer.answer_changes_count,
        time_to_first_choice_ms=answer.time_to_first_choice_ms,
        time_after_choice_ms=answer.time_after_choice_ms
    )

    # Update Elo ratings and aggregates
    try:
        # Update Elo ratings for user ability (theta_user)
        new_user_ability, _ = update_elo_ratings(
            user_aggregate.elo_ability,
            item_aggregate.elo_difficulty,  # Still used for Elo calculation, but not updated for real items
            is_correct_for_aggregates
        )

        # Update user aggregates (always update for both calibration and real)
        user_updates = update_user_aggregates(
            db_session.user_id,
            is_correct_for_aggregates,
            confidence_for_aggregates,
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
            is_correct_for_aggregates,
            confidence_for_aggregates,
            answer.response_time_ms,
            {
                'avg_accuracy': item_aggregate.avg_accuracy,
                'avg_confidence': item_aggregate.avg_confidence,
                'avg_conf_gap': item_aggregate.avg_conf_gap,
                'avg_time_ms': item_aggregate.avg_time_ms,
                'elo_difficulty': item_aggregate.elo_difficulty,
                'bb_alpha': item_aggregate.bb_alpha if hasattr(item_aggregate,
                                                               'bb_alpha') and item_aggregate.bb_alpha else 1.0,
                'bb_beta': item_aggregate.bb_beta if hasattr(item_aggregate,
                                                             'bb_beta') and item_aggregate.bb_beta else 1.0,
                'bb_n': item_aggregate.bb_n if hasattr(item_aggregate, 'bb_n') else 0
            }
        )

        # Update Beta-Binomial difficulty ONLY for real interactions
        if db_session.purpose == "real":
            new_bb_alpha, new_bb_beta = update_beta_binomial_difficulty(
                item_updates['bb_alpha'],
                item_updates['bb_beta'],
                is_correct_for_aggregates
            )
            item_updates['bb_alpha'] = new_bb_alpha
            item_updates['bb_beta'] = new_bb_beta
            item_updates['bb_n'] = item_updates.get('bb_n', 0) + 1
            item_updates['bb_updated_at'] = datetime.now(tz=timezone.utc)

        # Keep Elo difficulty for backward compatibility (but don't update it for real items)
        # For calibration, we can still update Elo if needed
        if db_session.purpose == "calibration":
            _, new_item_difficulty = update_elo_ratings(
                user_aggregate.elo_ability,
                item_aggregate.elo_difficulty,
                is_correct_for_aggregates
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


@router.post("/{session_id}/confidence-policy", response_model=ConfidencePolicyResponse)
async def get_confidence_policy(
        session_id: int,
        payload: ConfidencePolicyRequest,
        db: Session = Depends(get_db)
):
    db_session = get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_agg = get_or_create_user_aggregate(db, db_session.user_id)
    item_agg = get_or_create_item_aggregate(db, payload.item_id)
    item = get_item(db, payload.item_id)
    should_ask = _resolve_require_confidence(
        session_id=db_session.id,
        user_id=db_session.user_id,
        item_id=payload.item_id,
        answered_count=len(db_session.interactions),
        ema_conf_gap=float(user_agg.ema_conf_gap or 0.0),
        ema_accuracy=float(user_agg.ema_accuracy or 0.0),
        item_error_rate=1.0 - float(item_agg.avg_accuracy or 0.0),
        item_difficulty=float(item.difficulty_hint or 5.0) if item else 5.0,
    )
    sampling_rate = 1.0 if should_ask else 0.3

    return ConfidencePolicyResponse(
        should_request_confidence=should_ask,
        confidence_sampling_rate=sampling_rate,
        mode=db_session.mode
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
