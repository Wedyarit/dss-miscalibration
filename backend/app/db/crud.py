from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models import User, Item, Session as DBSession, Interaction, AggregateUser, AggregateItem, ModelRegistry
from typing import List, Optional
import json
from datetime import datetime

# User CRUD
def create_user(db: Session, role: str, display_name: Optional[str] = None) -> User:
    db_user = User(role=role, display_name=display_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_or_create_student_by_name(db: Session, display_name: str) -> User:
    normalized = (display_name or "").strip()
    if not normalized:
        normalized = "Student"
    user = (
        db.query(User)
        .filter(User.role == "student")
        .filter(func.lower(User.display_name) == normalized.lower())
        .first()
    )
    if user:
        return user
    return create_user(db, role="student", display_name=normalized)

def get_users_by_role(db: Session, role: str) -> List[User]:
    return db.query(User).filter(User.role == role).all()

# Item CRUD
def create_item(db: Session, stem_en: str, options_en: List[str], stem_ru: str = None, options_ru: List[str] = None, correct_option: int = 0, tags_en: List[str] = None, tags_ru: List[str] = None, difficulty_hint: float = None) -> Item:
    db_item = Item(
        stem_en=stem_en,
        options_en_json=json.dumps(options_en),
        stem_ru=stem_ru,
        options_ru_json=json.dumps(options_ru) if options_ru else None,
        correct_option=correct_option,
        tags_en=",".join(tags_en) if tags_en else "",
        tags_ru=",".join(tags_ru) if tags_ru else None,
        difficulty_hint=difficulty_hint
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_item(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[Item]:
    return db.query(Item).offset(skip).limit(limit).all()

def get_items_by_tags(db: Session, tags: List[str]) -> List[Item]:
    tag_filter = f"%{','.join(tags)}%"
    return db.query(Item).filter(Item.tags_en.like(tag_filter)).all()

def get_random_item(db: Session, exclude_ids: List[int] = None, language: str = 'en') -> Optional[Item]:
    query = db.query(Item)
    if exclude_ids:
        query = query.filter(~Item.id.in_(exclude_ids))
    return query.order_by(func.random()).first()

def get_localized_item(item: Item, language: str = 'en') -> dict:
    """Convert Item to localized format"""
    if language == 'ru' and item.stem_ru:
        return {
            'id': item.id,
            'stem': item.stem_ru,
            'options': json.loads(item.options_ru_json) if item.options_ru_json else json.loads(item.options_en_json),
            'correct_option': item.correct_option,
            'tags': item.tags_ru.split(',') if item.tags_ru else item.tags_en.split(','),
            'difficulty_hint': item.difficulty_hint,
            'created_at': item.created_at
        }
    else:
        return {
            'id': item.id,
            'stem': item.stem_en,
            'options': json.loads(item.options_en_json),
            'correct_option': item.correct_option,
            'tags': item.tags_en.split(',') if item.tags_en else [],
            'difficulty_hint': item.difficulty_hint,
            'created_at': item.created_at
        }

# Session CRUD
def create_session(db: Session, user_id: int, mode: str, purpose: str = "real") -> DBSession:
    db_session = DBSession(user_id=user_id, mode=mode, purpose=purpose)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: int) -> Optional[DBSession]:
    return db.query(DBSession).filter(DBSession.id == session_id).first()

def finish_session(db: Session, session_id: int):
    db.query(DBSession).filter(DBSession.id == session_id).update({"finished_at": datetime.utcnow()})
    db.commit()

# Interaction CRUD
def create_interaction(db: Session, session_id: int, user_id: int, item_id: int, 
                      chosen_option: int, is_correct: bool, confidence: Optional[float], 
                      response_time_ms: int, attempts_count: int = 1,
                      initial_chosen_option: Optional[str] = None,
                      initial_confidence: Optional[float] = None,
                      reconsidered: bool = False,
                      time_to_reconsider_ms: Optional[int] = None,
                      answer_changes_count: Optional[int] = None,
                      time_to_first_choice_ms: Optional[int] = None,
                      time_after_choice_ms: Optional[int] = None) -> Interaction:
    db_interaction = Interaction(
        session_id=session_id,
        user_id=user_id,
        item_id=item_id,
        chosen_option=chosen_option,
        initial_chosen_option=initial_chosen_option,
        is_correct=is_correct,
        confidence=confidence,
        initial_confidence=initial_confidence,
        reconsidered=reconsidered,
        time_to_reconsider_ms=time_to_reconsider_ms,
        response_time_ms=response_time_ms,
        attempts_count=attempts_count,
        answer_changes_count=answer_changes_count or 0,
        time_to_first_choice_ms=time_to_first_choice_ms,
        time_after_choice_ms=time_after_choice_ms
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

def get_interactions_by_session(db: Session, session_id: int) -> List[Interaction]:
    return db.query(Interaction).filter(Interaction.session_id == session_id).all()

def get_interactions_by_user(db: Session, user_id: int, limit: int = 100) -> List[Interaction]:
    return db.query(Interaction).filter(Interaction.user_id == user_id).order_by(desc(Interaction.timestamp)).limit(limit).all()

def get_interactions_for_training(db: Session, limit: int = 10000, purpose: str = "calibration") -> List[Interaction]:
    """
    Get interactions for training. By default, returns only calibration interactions.
    For calibration dataset: purpose='calibration' and confidence is not None.
    """
    query = db.query(Interaction).join(DBSession).filter(DBSession.purpose == purpose)
    if purpose == "calibration":
        # For calibration, we need confidence from initial or final answer.
        query = query.filter(
            (Interaction.initial_confidence.isnot(None)) | (Interaction.confidence.isnot(None))
        )
    return query.limit(limit).all()

# Aggregate CRUD
def get_or_create_user_aggregate(db: Session, user_id: int) -> AggregateUser:
    aggregate = db.query(AggregateUser).filter(AggregateUser.user_id == user_id).first()
    if not aggregate:
        aggregate = AggregateUser(user_id=user_id)
        db.add(aggregate)
        db.commit()
        db.refresh(aggregate)
    return aggregate

def get_or_create_item_aggregate(db: Session, item_id: int) -> AggregateItem:
    aggregate = db.query(AggregateItem).filter(AggregateItem.item_id == item_id).first()
    if not aggregate:
        aggregate = AggregateItem(
            item_id=item_id,
            bb_alpha=1.0,  # Laplace prior
            bb_beta=1.0,
            bb_n=0
        )
        db.add(aggregate)
        db.commit()
        db.refresh(aggregate)
    # Ensure BB fields are initialized (for backward compatibility with existing records)
    if aggregate.bb_alpha is None or aggregate.bb_alpha == 0:
        aggregate.bb_alpha = 1.0
    if aggregate.bb_beta is None or aggregate.bb_beta == 0:
        aggregate.bb_beta = 1.0
    if aggregate.bb_n is None:
        aggregate.bb_n = 0
    return aggregate

def update_user_aggregate(db: Session, user_id: int, **kwargs):
    aggregate = get_or_create_user_aggregate(db, user_id)
    for key, value in kwargs.items():
        setattr(aggregate, key, value)
    aggregate.updated_at = datetime.utcnow()
    db.commit()

def update_item_aggregate(db: Session, item_id: int, **kwargs):
    aggregate = get_or_create_item_aggregate(db, item_id)
    for key, value in kwargs.items():
        setattr(aggregate, key, value)
    aggregate.updated_at = datetime.utcnow()
    db.commit()

# Model Registry CRUD
def create_model_registry(db: Session, version: str, params_json: str, calib_type: str, 
                         ece: Optional[float] = None, brier: Optional[float] = None, 
                         roc_auc: Optional[float] = None, notes: Optional[str] = None,
                         friendly_name: Optional[str] = None, is_active: bool = True) -> ModelRegistry:
    if is_active:
        db.query(ModelRegistry).update({"is_active": False})
    db_model = ModelRegistry(
        version=version,
        friendly_name=friendly_name,
        is_active=is_active,
        params_json=params_json,
        calib_type=calib_type,
        ece=ece,
        brier=brier,
        roc_auc=roc_auc,
        notes=notes
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_latest_model(db: Session) -> Optional[ModelRegistry]:
    active = (
        db.query(ModelRegistry)
        .filter(ModelRegistry.is_active == True)  # noqa: E712
        .order_by(desc(ModelRegistry.trained_at))
        .first()
    )
    if active:
        return active
    return db.query(ModelRegistry).order_by(desc(ModelRegistry.trained_at)).first()

def get_model_by_version(db: Session, version: str) -> Optional[ModelRegistry]:
    return db.query(ModelRegistry).filter(ModelRegistry.version == version).first()
