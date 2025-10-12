import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.db.crud import get_user, get_item, get_or_create_user_aggregate, get_or_create_item_aggregate, get_latest_model
from app.db.session import SessionLocal
from app.ml.calibrate import load_model
from app.ml.features import extract_user_features, extract_item_features, extract_interaction_features, \
    extract_temporal_features, create_feature_vector


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
                    "risk": 0.5,
                    "recommendation": "proceed",
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
                "risk": 0.5,
                "recommendation": "proceed",
                "model_version": model_version,
                "error": "Failed to load model"
            }

        # Get user and item data
        user = get_user(db, user_id)
        item = get_item(db, item_id)

        if user is None or item is None:
            return {
                "risk": 0.5,
                "recommendation": "proceed",
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

        item_agg_dict = {
            'elo_difficulty': item_aggregate.elo_difficulty,
            'avg_accuracy': item_aggregate.avg_accuracy,
            'avg_time_ms': item_aggregate.avg_time_ms
        }

        item_data = {
            'tags': item.tags_en.split(',') if item.tags_en else [],
            'difficulty_hint': item.difficulty_hint
        }

        # Extract features
        user_features = extract_user_features(user_id, user_agg_dict, [])
        item_features = extract_item_features(item_id, item_agg_dict, item_data)
        interaction_features = extract_interaction_features(interaction_data)
        temporal_features = extract_temporal_features(interaction_data.get('timestamp', datetime.utcnow()))

        # Create feature vector
        feature_vector = create_feature_vector(user_features, item_features, interaction_features, temporal_features)

        # Make prediction
        risk = model.predict_proba(feature_vector.reshape(1, -1))[0]

        # Generate recommendation
        recommendation = "review_answer" if risk >= 0.5 else "proceed"

        return {
            "risk": float(risk),
            "recommendation": recommendation,
            "model_version": model_version,
            "features_used": len(feature_vector)
        }

    except Exception as e:
        return {
            "risk": 0.5,
            "recommendation": "proceed",
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
