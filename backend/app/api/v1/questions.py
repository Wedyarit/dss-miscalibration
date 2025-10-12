from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.crud import create_item, get_item, get_items, get_random_item, get_items_by_tags, get_localized_item
from app.db.models import Interaction
from app.schemas.questions import QuestionCreate, QuestionResponse, QuestionList
from typing import List, Optional
import json

router = APIRouter()

@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    """Create a new question (admin only)"""
    try:
        db_question = create_item(
            db=db,
            stem_en=question.stem_en,
            options_en=question.options_en,
            stem_ru=question.stem_ru,
            options_ru=question.options_ru,
            correct_option=question.correct_option,
            tags_en=question.tags_en,
            tags_ru=question.tags_ru,
            difficulty_hint=question.difficulty_hint
        )
        
        # Return the English version by default for creation confirmation
        return QuestionResponse(
            id=db_question.id,
            stem=db_question.stem_en,
            options=json.loads(db_question.options_en_json),
            correct_option=db_question.correct_option,
            tags=db_question.tags_en.split(',') if db_question.tags_en else [],
            difficulty_hint=db_question.difficulty_hint,
            created_at=db_question.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{item_id}", response_model=QuestionResponse)
async def get_question(
    item_id: int,
    language: str = Query("en", description="Language preference (en/ru)"),
    db: Session = Depends(get_db)
):
    """Get a specific question"""
    db_question = get_item(db, item_id)
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    localized_question = get_localized_item(db_question, language)
    
    return QuestionResponse(
        id=localized_question['id'],
        stem=localized_question['stem'],
        options=localized_question['options'],
        correct_option=localized_question['correct_option'],
        tags=localized_question['tags'],
        difficulty_hint=localized_question['difficulty_hint'],
        created_at=localized_question['created_at']
    )

@router.get("/", response_model=QuestionList)
async def list_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    language: str = Query("en", description="Language preference (en/ru)"),
    db: Session = Depends(get_db)
):
    """List questions with optional filtering"""
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        questions = get_items_by_tags(db, tag_list)
    else:
        questions = get_items(db, skip=skip, limit=limit)
    
    question_responses = []
    for q in questions:
        localized_q = get_localized_item(q, language)
        question_responses.append(QuestionResponse(
            id=localized_q['id'],
            stem=localized_q['stem'],
            options=localized_q['options'],
            correct_option=localized_q['correct_option'],
            tags=localized_q['tags'],
            difficulty_hint=localized_q['difficulty_hint'],
            created_at=localized_q['created_at']
        ))
    
    return QuestionList(
        questions=question_responses,
        total=len(question_responses),
        page=skip // limit + 1,
        size=limit
    )

@router.get("/next/random", response_model=QuestionResponse)
async def get_next_random_question(
    session_id: Optional[int] = Query(None, description="Session ID to avoid already answered questions"),
    language: str = Query("en", description="Language preference (en/ru)"),
    db: Session = Depends(get_db)
):
    """Get a random question for testing, avoiding already answered questions in the session"""
    # Get already answered question IDs for this session
    answered_item_ids = []
    if session_id:
        answered_interactions = db.query(Interaction).filter(
            Interaction.session_id == session_id
        ).all()
        answered_item_ids = [interaction.item_id for interaction in answered_interactions]
    
    db_question = get_random_item(db, exclude_ids=answered_item_ids, language=language)
    if not db_question:
        raise HTTPException(status_code=404, detail="No questions available")
    
    # Convert to localized format
    localized_question = get_localized_item(db_question, language)
    
    return QuestionResponse(
        id=localized_question['id'],
        stem=localized_question['stem'],
        options=localized_question['options'],
        correct_option=localized_question['correct_option'],
        tags=localized_question['tags'],
        difficulty_hint=localized_question['difficulty_hint'],
        created_at=localized_question['created_at']
    )
