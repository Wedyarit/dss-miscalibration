import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from app.core.config import settings
from app.db.crud import get_user, get_item, get_or_create_user_aggregate, get_or_create_item_aggregate, get_latest_model
from app.db.session import SessionLocal
from app.ml.calibrate import load_model
from app.ml.features import extract_user_features, extract_item_features, extract_interaction_features, \
    extract_temporal_features, create_feature_vector


def _confidence_sampling_rate(ema_conf_gap: float, ema_accuracy: float) -> float:
    """
    If the student is already well-calibrated, ask confidence less often.
    Otherwise keep confidence collection dense for better adaptation.
    """
    well_calibrated = abs(ema_conf_gap) <= 0.08 and ema_accuracy >= 0.65
    return 0.3 if well_calibrated else 1.0


def _stable_bucket(user_id: int, item_id: int, timestamp: datetime) -> float:
    payload = f"{user_id}:{item_id}:{timestamp.isoformat()}"
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()
    # 0..1 stable pseudo-random bucket
    return (int(digest[:8], 16) % 1000) / 1000.0


def should_request_confidence(
    user_id: int,
    item_id: int,
    ema_conf_gap: float,
    ema_accuracy: float,
    timestamp: Optional[datetime] = None,
) -> Tuple[bool, float]:
    ts = timestamp or datetime.now(tz=timezone.utc)
    sampling_rate = _confidence_sampling_rate(ema_conf_gap, ema_accuracy)
    ask_confidence = _stable_bucket(user_id, item_id, ts) <= sampling_rate
    return ask_confidence, sampling_rate


def _reason_for_risk(
    risk: float,
    interaction_data: Dict,
    user_agg_dict: Dict,
    item_data: Dict,
    item_agg_dict: Dict,
) -> Tuple[str, str]:
    response_time_ms = int(interaction_data.get("response_time_ms") or 0)
    attempts_count = int(interaction_data.get("attempts_count") or 1)
    confidence = interaction_data.get("confidence")
    difficulty_hint = item_data.get("difficulty_hint") or 5.0
    item_error_proxy = 1.0 - float(item_agg_dict.get("avg_accuracy") or 0.5)
    user_conf_gap = float(user_agg_dict.get("ema_conf_gap") or 0.0)

    if risk < 0.5:
        return (
            "LOW_RISK_CONTINUE",
            "Student behavior is consistent with stable calibration on this item.",
        )

    if response_time_ms > 0 and response_time_ms < 3500 and difficulty_hint >= 6.0:
        return (
            "FAST_ANSWER_COMPLEX_TOPIC",
            "The answer was submitted very quickly for a relatively complex topic.",
        )

    if confidence is not None and confidence >= 0.75 and (item_error_proxy >= 0.45 or user_conf_gap >= 0.12):
        return (
            "SURE_ERROR_PRONE_DOMAIN",
            "High confidence in a domain where errors are historically common.",
        )

    if attempts_count > 1:
        return (
            "STREAK_BREAK_RISK",
            "Multiple attempts suggest uncertainty after an initial decision.",
        )

    return (
        "STREAK_BREAK_RISK",
        "Current interaction pattern indicates elevated miscalibration risk.",
    )


def _message_ru_for_reason(reason_code: str) -> str:
    messages = {
        "FAST_ANSWER_COMPLEX_TOPIC": "Вы ответили очень быстро для такого сложного вопроса. Проверьте детали.",
        "SURE_ERROR_PRONE_DOMAIN": "Вы были очень уверены в теме, где часто возникают ошибки. Перепроверьте ход рассуждения.",
        "STREAK_BREAK_RISK": "Сделайте короткую аналитическую паузу и проверьте логику ответа.",
        "LOW_RISK_CONTINUE": "Короткая пауза: проверьте, не пропущена ли важная деталь.",
        "MODEL_UNAVAILABLE": "Сделайте короткую паузу и перепроверьте ключевую идею.",
        "MODEL_LOAD_FAILED": "Сделайте короткую паузу и перепроверьте ключевую идею.",
        "MISSING_CONTEXT": "Сделайте короткую паузу и перепроверьте ключевую идею.",
        "INFERENCE_ERROR": "Сделайте короткую паузу и перепроверьте ключевую идею.",
        "SOFT_RANDOM_NUDGE": "Этот вопрос часто вызывает путаницу, вы уверены в логике?",
    }
    return messages.get(reason_code, "Сделайте короткую аналитическую паузу и проверьте логику ответа.")


def _stable_noise_bucket(user_id: int, item_id: int, timestamp: datetime) -> float:
    payload = f"noise:{user_id}:{item_id}:{timestamp.isoformat()}"
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 1000) / 1000.0


def predict_confident_error(user_id: int, item_id: int, interaction_data: Dict,
                            model_version: Optional[str] = None) -> Dict[str, Any]:
    """Predict confident error risk for a single interaction"""

    db = SessionLocal()
    try:
        # Get latest model if no version specified
        if model_version is None:
            latest_model = get_latest_model(db)
            if latest_model is None:
                return {
                    "intervention": {
                        "risk": 0.5,
                        "reason_code": "MODEL_UNAVAILABLE",
                        "message_ru": _message_ru_for_reason("MODEL_UNAVAILABLE"),
                        "show_intervention": True,
                    },
                    "model_version": None,
                    "error": "No trained model available"
                }
            model_version = latest_model.version

        # Load model
        else:
            latest_model = get_latest_model(db)

        model_path = None
        if latest_model is not None and latest_model.params_json:
            try:
                params = json.loads(latest_model.params_json)
                mp = params.get("model_path")
                if mp and os.path.exists(mp):
                    model_path = mp
            except Exception:
                pass
        if model_path is None:
            model_path = os.path.abspath(os.path.join(settings.MODELS_DIR, f"model_{model_version}.pkl"))

        # Load model
        model = load_model(model_path)

        if model is None:
            return {
                "intervention": {
                    "risk": 0.5,
                    "reason_code": "MODEL_LOAD_FAILED",
                    "message_ru": _message_ru_for_reason("MODEL_LOAD_FAILED"),
                    "show_intervention": True,
                },
                "model_version": model_version,
                "error": "Failed to load model"
            }

        # Get user and item data
        user = get_user(db, user_id)
        item = get_item(db, item_id)

        if user is None or item is None:
            return {
                "intervention": {
                    "risk": 0.5,
                    "reason_code": "MISSING_CONTEXT",
                    "message_ru": _message_ru_for_reason("MISSING_CONTEXT"),
                    "show_intervention": True,
                },
                "model_version": model_version,
                "error": "User or item not found"
            }

        # Get aggregates
        user_aggregate = get_or_create_user_aggregate(db, user_id)
        item_aggregate = get_or_create_item_aggregate(db, item_id)

        # Convert aggregates to dict format
        user_agg_dict = {
            'ema_accuracy': user_aggregate.ema_accuracy,
            'ema_confidence': user_aggregate.ema_confidence,
            'ema_conf_gap': user_aggregate.ema_conf_gap,
            'elo_ability': user_aggregate.elo_ability,
            'avg_time_ms': user_aggregate.avg_time_ms
        }

        # Get Beta-Binomial parameters
        bb_alpha = getattr(item_aggregate, 'bb_alpha', 1.0) if hasattr(item_aggregate, 'bb_alpha') else 1.0
        bb_beta = getattr(item_aggregate, 'bb_beta', 1.0) if hasattr(item_aggregate, 'bb_beta') else 1.0

        item_agg_dict = {
            'bb_alpha': bb_alpha,
            'bb_beta': bb_beta,
            'elo_difficulty': item_aggregate.elo_difficulty,  # Legacy
            'avg_accuracy': item_aggregate.avg_accuracy,
            'avg_time_ms': item_aggregate.avg_time_ms
        }

        item_data = {
            'tags': item.tags_en.split(',') if item.tags_en else [],
            'difficulty_hint': item.difficulty_hint
        }

        # Extract features
        # Note: interaction_data may not have confidence (for real tests)
        user_features = extract_user_features(user_id, user_agg_dict, [])
        item_features = extract_item_features(item_id, item_agg_dict, item_data)
        # Don't require confidence in interaction_data - model works without it
        interaction_features = extract_interaction_features(interaction_data)
        temporal_features = extract_temporal_features(interaction_data.get('timestamp', datetime.now(tz=timezone.utc)))

        # Create feature vector
        feature_vector = create_feature_vector(user_features, item_features, interaction_features, temporal_features)

        # Make prediction
        risk = model.predict_proba(feature_vector.reshape(1, -1))[0]

        reason_code, reason_text = _reason_for_risk(
            float(risk), interaction_data, user_agg_dict, item_data, item_agg_dict
        )
        timestamp = interaction_data.get("timestamp") or datetime.now(tz=timezone.utc)
        show_intervention = float(risk) >= 0.5
        message_ru = _message_ru_for_reason(reason_code)

        # Noise-injection: in 15% of low-risk cases still trigger a soft nudge.
        if not show_intervention and _stable_noise_bucket(user_id, item_id, timestamp) < 0.15:
            show_intervention = True
            reason_code = "SOFT_RANDOM_NUDGE"
            reason_text = "Randomized soft nudge to prevent detector abuse."
            message_ru = _message_ru_for_reason(reason_code)

        return {
            "intervention": {
                "risk": float(risk),
                "reason_code": reason_code,
                "message_ru": message_ru,
                "show_intervention": show_intervention,
                "reason_text": reason_text,
            },
            "model_version": model_version,
            "features_used": len(feature_vector)
        }

    except Exception as e:
        return {
            "intervention": {
                "risk": 0.5,
                "reason_code": "INFERENCE_ERROR",
                "message_ru": _message_ru_for_reason("INFERENCE_ERROR"),
                "show_intervention": True,
            },
            "model_version": model_version,
            "error": str(e)
        }
    finally:
        db.close()


def predict_batch(interactions: List[Dict], model_version: Optional[str] = None) -> List[Dict]:
    """Predict confident error risk for multiple interactions"""

    results = []
    for interaction in interactions:
        result = predict_confident_error(
            interaction['user_id'],
            interaction['item_id'],
            interaction,
            model_version
        )
        results.append(result)

    return results
