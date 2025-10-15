from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from sklearn.metrics import roc_auc_score
from app.core.config import settings
from app.db.session import get_db
from app.db.crud import get_interactions_for_training, get_latest_model, get_items, get_item
from app.db.models import Interaction
import numpy as np
from app.schemas.analytics import AnalyticsOverview, ReliabilityResponse, ReliabilityBin, ProblematicItemsResponse, ProblematicItem, ExportRequest
from app.ml.metrics import calculate_all_metrics, reliability_diagram_data, confident_error_rate
from app.ml.inference import predict_confident_error
from typing import List, Optional
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

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(db: Session = Depends(get_db)):
    interactions = get_interactions_for_training(db, limit=10000)

    if len(interactions) < 10:
        return AnalyticsOverview(
            ece=0.0,
            mce=0.0,
            brier=0.0,
            roc_auc=0.5,
            confident_error_rate=0.0,
            total_interactions=len(interactions),
            interactions_with_confidence=len([i for i in interactions if i.confidence is not None]),
            model_version=None
        )

    y_acc = []
    y_conf = []
    for interaction in interactions:
        if interaction.confidence is not None:
            y_acc.append(1 if interaction.is_correct else 0)
            y_conf.append(interaction.confidence)

    if len(y_acc) < 10:
        return AnalyticsOverview(
            ece=0.0,
            mce=0.0,
            brier=0.0,
            roc_auc=0.5,
            confident_error_rate=0.0,
            total_interactions=len(interactions),
            interactions_with_confidence=len(y_acc),
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
        model_version=model_version
    )

@router.get("/reliability", response_model=ReliabilityResponse)
async def get_reliability_data(
    n_bins: int = 10,
    db: Session = Depends(get_db)
):
    """Get reliability diagram data"""

    interactions = get_interactions_for_training(db, limit=10000)

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
        if interaction.confidence is not None:
            y_true.append(1 if interaction.is_correct else 0)  # Accuracy target
            y_prob.append(interaction.confidence)

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
    """Get items with highest confident error rates"""

    # Get all items
    items = get_items(db, limit=1000)
    problematic_items = []

    for item in items:
        # Get interactions for this item
        interactions = db.query(Interaction).filter(Interaction.item_id == item.id).all()

        if len(interactions) < min_interactions:
            continue

        # Calculate metrics
        confident_interactions = [i for i in interactions if i.confidence is not None and i.confidence >= threshold]
        if len(confident_interactions) == 0:
            continue

        confident_errors = [i for i in confident_interactions if not i.is_correct]
        confident_error_rate = len(confident_errors) / len(confident_interactions)

        avg_confidence = sum(i.confidence for i in confident_interactions) / len(confident_interactions)
        avg_accuracy = sum(1 if i.is_correct else 0 for i in interactions) / len(interactions)

        problematic_items.append(ProblematicItem(
            item_id=item.id,
            stem=get_localized_stem(item, language)[:100] + "..." if len(get_localized_stem(item, language)) > 100 else get_localized_stem(item, language),
            tags=get_localized_tags(item, language),
            confident_error_rate=confident_error_rate,
            total_interactions=len(interactions),
            avg_confidence=avg_confidence,
            avg_accuracy=avg_accuracy
        ))

    # Sort by confident error rate
    problematic_items.sort(key=lambda x: x.confident_error_rate, reverse=True)

    return ProblematicItemsResponse(
        items=problematic_items[:20],  # Top 20
        total_items=len(problematic_items),
        threshold=threshold
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
        'is_correct', 'confidence', 'response_time_ms', 'attempts_count', 'timestamp'
    ])

    # Write data
    for interaction in interactions:
        writer.writerow([
            interaction.id,
            interaction.session_id,
            interaction.user_id,
            interaction.item_id,
            interaction.chosen_option,
            interaction.is_correct,
            interaction.confidence,
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
