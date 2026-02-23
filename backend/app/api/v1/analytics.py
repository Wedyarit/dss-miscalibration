from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from sklearn.metrics import roc_auc_score
from app.core.config import settings
from app.db.session import get_db
from app.db.crud import get_interactions_for_training, get_latest_model, get_items, get_or_create_item_aggregate
from app.db.models import Interaction, User
from app.ml.irt_elo import get_bb_difficulty
import numpy as np
from app.schemas.analytics import AnalyticsOverview, ReliabilityResponse, ReliabilityBin, ProblematicItemsResponse, ProblematicItem, InstructorSummaryResponse, InstructorInsight, HiddenStar
from app.ml.metrics import calculate_all_metrics, reliability_diagram_data, confident_error_rate
from typing import Optional, List
import csv
import io
from datetime import datetime

def get_localized_stem(item, language: str) -> str:
    """Get localized stem based on language"""
    if language == 'ru' and item.stem_ru:
        return item.stem_ru
    return item.stem_en

def get_localized_tags(item, language: str) -> list:
    """Get localized tags based on language"""
    if language == 'ru' and item.tags_ru:
        return item.tags_ru.split(',') if item.tags_ru else []
    return item.tags_en.split(',') if item.tags_en else []


def _parse_initial_option(raw_value):
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _effective_confidence(interaction: Interaction):
    return (
        interaction.initial_confidence
        if interaction.initial_confidence is not None
        else interaction.confidence
    )


def _effective_is_correct_for_calibration(interaction: Interaction):
    initial_option = _parse_initial_option(interaction.initial_chosen_option)
    if initial_option is None:
        return interaction.is_correct
    if interaction.item is None:
        return interaction.is_correct
    return initial_option == interaction.item.correct_option


def _coachability_rate(db: Session) -> float:
    interventions = (
        db.query(Interaction)
        .filter(Interaction.initial_chosen_option.isnot(None))
        .all()
    )
    if not interventions:
        return 0.0

    corrected = 0
    opportunities = 0
    for inter in interventions:
        initial_option = _parse_initial_option(inter.initial_chosen_option)
        if initial_option is None or inter.item is None:
            continue
        initial_is_correct = initial_option == inter.item.correct_option
        if initial_is_correct:
            continue
        opportunities += 1
        if inter.is_correct:
            corrected += 1
    if opportunities == 0:
        return 0.0
    return corrected / opportunities

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(db: Session = Depends(get_db)):
    """Get calibration quality metrics (ECE/MCE/Brier) from calibration dataset"""
    # Get only calibration interactions (where confidence is available)
    interactions = get_interactions_for_training(db, limit=10000, purpose="calibration")

    if len(interactions) < 10:
        return AnalyticsOverview(
            ece=0.0,
            mce=0.0,
            brier=0.0,
            roc_auc=0.5,
            confident_error_rate=0.0,
            total_interactions=len(interactions),
            interactions_with_confidence=len([i for i in interactions if _effective_confidence(i) is not None]),
            coachability_rate=_coachability_rate(db),
            model_version=None
        )

    y_acc = []
    y_conf = []
    for interaction in interactions:
        eff_conf = _effective_confidence(interaction)
        if eff_conf is not None:
            y_acc.append(1 if _effective_is_correct_for_calibration(interaction) else 0)
            y_conf.append(eff_conf)

    if len(y_acc) < 10:
        return AnalyticsOverview(
            ece=0.0,
            mce=0.0,
            brier=0.0,
            roc_auc=0.5,
            confident_error_rate=0.0,
            total_interactions=len(interactions),
            interactions_with_confidence=len(y_acc),
            coachability_rate=_coachability_rate(db),
            model_version=None
        )

    y_acc = np.array(y_acc)
    y_conf = np.array(y_conf)

    metrics = calculate_all_metrics(y_acc, y_conf)

    conf_thr = getattr(settings, "CONF_THRESHOLD", 0.7)
    cer = confident_error_rate(y_acc, y_conf, confidence_threshold=conf_thr)

    try:
        roc_auc_err = roc_auc_score(1 - y_acc, 1 - y_conf)
    except Exception:
        roc_auc_err = 0.5

    latest_model = get_latest_model(db)
    model_version = latest_model.version if latest_model else None

    return AnalyticsOverview(
        ece=metrics['ece'],
        mce=metrics['mce'],
        brier=metrics['brier'],
        roc_auc=roc_auc_err,
        confident_error_rate=cer,
        total_interactions=len(interactions),
        interactions_with_confidence=int(len(y_acc)),
        coachability_rate=_coachability_rate(db),
        model_version=model_version
    )

@router.get("/reliability", response_model=ReliabilityResponse)
async def get_reliability_data(
    n_bins: int = 10,
    db: Session = Depends(get_db)
):
    """Get reliability diagram data for calibration dataset"""

    interactions = get_interactions_for_training(db, limit=10000, purpose="calibration")

    if len(interactions) < 10:
        return ReliabilityResponse(
            bins=[],
            n_bins=n_bins,
            model_version=None
        )

    # Prepare data
    y_true = []
    y_prob = []

    for interaction in interactions:
        eff_conf = _effective_confidence(interaction)
        if eff_conf is not None:
            y_true.append(1 if _effective_is_correct_for_calibration(interaction) else 0)
            y_prob.append(eff_conf)

    if len(y_true) < 10:
        return ReliabilityResponse(
            bins=[],
            n_bins=n_bins,
            model_version=None
        )

    # Generate reliability diagram data
    reliability_data = reliability_diagram_data(
        np.array(y_true),
        np.array(y_prob),
        n_bins
    )

    bins = [ReliabilityBin(**bin_data) for bin_data in reliability_data]

    # Get latest model version
    latest_model = get_latest_model(db)
    model_version = latest_model.version if latest_model else None

    return ReliabilityResponse(
        bins=bins,
        n_bins=n_bins,
        model_version=model_version
    )

@router.get("/items/problematic", response_model=ProblematicItemsResponse)
async def get_problematic_items(
    threshold: float = 0.7,
    min_interactions: int = 5,
    language: str = Query("en", description="Language preference (en/ru)"),
    db: Session = Depends(get_db)
):
    """Get items with highest difficulty (Beta-Binomial p_error) and/or uncertainty

    Updated to use Beta-Binomial difficulty instead of confident error rate,
    since confidence may not be available in real tests.
    """

    # Get all items
    items = get_items(db, limit=1000)
    problematic_items = []

    for item in items:
        # Get item aggregate with BB parameters
        item_aggregate = get_or_create_item_aggregate(db, item.id)

        # Use Beta-Binomial difficulty
        bb_alpha = getattr(item_aggregate, 'bb_alpha', 1.0) if hasattr(item_aggregate, 'bb_alpha') else 1.0
        bb_beta = getattr(item_aggregate, 'bb_beta', 1.0) if hasattr(item_aggregate, 'bb_beta') else 1.0
        bb_n = getattr(item_aggregate, 'bb_n', 0) if hasattr(item_aggregate, 'bb_n') else 0

        if bb_n < min_interactions:
            continue

        # Calculate BB difficulty metrics
        bb_metrics = get_bb_difficulty(bb_alpha, bb_beta)
        p_error = bb_metrics['p_error']
        uncertainty = bb_metrics['uncertainty']

        # Get all interactions for this item (for avg_accuracy)
        interactions = db.query(Interaction).filter(Interaction.item_id == item.id).all()
        if len(interactions) == 0:
            continue

        avg_accuracy = sum(1 if i.is_correct else 0 for i in interactions) / len(interactions)

        # For backward compatibility, try to calculate confident_error_rate if we have calibration data
        confident_interactions = [i for i in interactions if i.confidence is not None and i.confidence >= threshold]
        if len(confident_interactions) > 0:
            confident_errors = [i for i in confident_interactions if not i.is_correct]
            confident_error_rate = len(confident_errors) / len(confident_interactions)
            avg_confidence = sum(i.confidence for i in confident_interactions) / len(confident_interactions)
        else:
            # Use p_error as proxy for confident_error_rate when confidence data is unavailable
            confident_error_rate = p_error
            avg_confidence = 0.0

        problematic_items.append(ProblematicItem(
            item_id=item.id,
            stem=get_localized_stem(item, language)[:100] + "..." if len(get_localized_stem(item, language)) > 100 else get_localized_stem(item, language),
            tags=get_localized_tags(item, language),
            confident_error_rate=confident_error_rate,  # Now based on BB p_error for real items
            total_interactions=len(interactions),
            avg_confidence=avg_confidence,
            avg_accuracy=avg_accuracy,
            pedagogical_note=(
                "This question might be misleading: many students are confident but wrong."
                if confident_error_rate >= 0.8 and avg_accuracy <= 0.45
                else "Students need concept reinforcement before this item."
            ),
            recommendation_for_teacher=(
                "Пересмотреть формулировку вопроса"
                if confident_error_rate >= 0.8 and avg_accuracy <= 0.45
                else "Провести доп. занятие по теме"
            ),
        ))

    # Sort by confident_error_rate (which is now p_error for real items)
    problematic_items.sort(key=lambda x: x.confident_error_rate, reverse=True)

    return ProblematicItemsResponse(
        items=problematic_items[:20],  # Top 20
        total_items=len(problematic_items),
        threshold=threshold
    )

@router.get("/instructor/summary", response_model=InstructorSummaryResponse)
async def get_instructor_summary(
    n_bins: int = 10,
    threshold: float = 0.7,
    min_interactions: int = 5,
    language: str = Query("en", description="Language preference (en/ru)"),
    db: Session = Depends(get_db)
):
    overview = await get_analytics_overview(db)
    reliability = await get_reliability_data(n_bins=n_bins, db=db)
    problematic = await get_problematic_items(
        threshold=threshold, min_interactions=min_interactions, language=language, db=db
    )

    if overview.ece <= 0.08:
        self_awareness = "High"
    elif overview.ece <= 0.18:
        self_awareness = "Medium"
    else:
        self_awareness = "Low"

    danger_zones = []
    for item in problematic.items[:5]:
        if item.tags:
            danger_zones.extend(item.tags)
    # keep order while deduplicating
    danger_zones = list(dict.fromkeys(danger_zones))[:5]

    hidden_stars: List[HiddenStar] = []
    user_rows = (
        db.query(
            Interaction.user_id.label("user_id"),
            func.avg(func.cast(Interaction.is_correct, Integer)).label("accuracy"),
            func.avg(Interaction.confidence).label("avg_confidence"),
            func.count(Interaction.id).label("n"),
        )
        .filter(Interaction.confidence.isnot(None))
        .group_by(Interaction.user_id)
        .having(func.count(Interaction.id) >= 5)
        .all()
    )
    for row in user_rows:
        acc = float(row.accuracy or 0.0)
        conf = float(row.avg_confidence or 0.0)
        if acc >= 0.75 and conf <= 0.45:
            user = db.query(User).filter(User.id == row.user_id).first()
            hidden_stars.append(
                HiddenStar(
                    user_id=row.user_id,
                    student_name=(user.display_name if user and user.display_name else f"Student {row.user_id}"),
                    accuracy=acc,
                    avg_confidence=conf,
                )
            )
    hidden_stars = hidden_stars[:5]

    insights = [
        InstructorInsight(
            key="class_self_awareness",
            label="Здоровье калибровки",
            value=self_awareness,
            description="Overall ability to match confidence to real performance.",
        ),
        InstructorInsight(
            key="danger_zones",
            label="Зоны ложной уверенности",
            value=", ".join(danger_zones) if danger_zones else "No clear zone yet",
            description="Topics where students are frequently confident but wrong.",
        ),
        InstructorInsight(
            key="hidden_stars",
            label="Скрытый потенциал",
            value=str(len(hidden_stars)),
            description="Accurate students with low confidence (possible imposter syndrome).",
        ),
    ]

    return InstructorSummaryResponse(
        overview=overview,
        reliability=reliability,
        class_self_awareness=self_awareness,
        danger_zones=danger_zones,
        hidden_stars=hidden_stars,
        insights=insights,
        problematic_items=problematic.items,
    )

@router.get("/export/interactions")
async def export_interactions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Export interactions as CSV"""

    # Build query
    query = db.query(Interaction)

    if start_date:
        query = query.filter(Interaction.timestamp >= start_date)
    if end_date:
        query = query.filter(Interaction.timestamp <= end_date)
    if user_id:
        query = query.filter(Interaction.user_id == user_id)
    if session_id:
        query = query.filter(Interaction.session_id == session_id)

    interactions = query.limit(10000).all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'id', 'session_id', 'user_id', 'item_id', 'chosen_option',
        'initial_chosen_option', 'is_correct', 'confidence', 'initial_confidence',
        'reconsidered', 'time_to_reconsider_ms', 'response_time_ms', 'attempts_count', 'timestamp'
    ])

    # Write data
    for interaction in interactions:
        writer.writerow([
            interaction.id,
            interaction.session_id,
            interaction.user_id,
            interaction.item_id,
            interaction.chosen_option,
            interaction.initial_chosen_option,
            interaction.is_correct,
            interaction.confidence,
            interaction.initial_confidence,
            interaction.reconsidered,
            interaction.time_to_reconsider_ms,
            interaction.response_time_ms,
            interaction.attempts_count,
            interaction.timestamp.isoformat()
        ])

    # Return CSV response
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=interactions.csv"}
    )
