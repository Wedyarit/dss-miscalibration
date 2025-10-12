from sklearn.model_selection import train_test_split
from app.ml.features import prepare_training_data
from app.ml.calibrate import calibrate_model, save_model
from app.ml.metrics import calculate_all_metrics, confident_error_rate
from app.db.crud import get_interactions_for_training, create_model_registry
from app.db.session import SessionLocal
from typing import Dict, List, Tuple
import numpy as np
import json
from datetime import datetime
import os
from app.core.config import settings

def find_suitable_threshold(interaction_data: List[Dict], min_samples_per_class: int = 2) -> float:
    """Find the highest confidence threshold that still has enough samples for each class"""
    thresholds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

    for threshold in thresholds:
        # Filter interactions by confidence threshold
        filtered_data = [
            data for data in interaction_data
            if data.get('confidence') is not None and data.get('confidence') >= threshold
        ]

        if len(filtered_data) < min_samples_per_class * 2:
            continue

        # Check class distribution
        targets = [data['is_correct'] for data in filtered_data]
        unique_classes, class_counts = np.unique(targets, return_counts=True)
        min_class_count = np.min(class_counts)

        if min_class_count >= min_samples_per_class:
            return threshold

    return 0.1  # Fallback to very low threshold

def train_model(confidence_threshold: float = 0.7,
                calibration: str = "platt",
                bins: int = 10,
                test_size: float = 0.2) -> Dict:
    """Train the miscalibration prediction model"""

    db = SessionLocal()
    try:
        # Get training data
        interactions = get_interactions_for_training(db, limit=10000)

        if len(interactions) < 50:
            return {
                "success": False,
                "error": "Insufficient training data. Need at least 50 interactions with confidence scores."
            }

        # Convert interactions to dict format for feature extraction
        interaction_data = []
        for interaction in interactions:
            interaction_data.append({
                'user_id': interaction.user_id,
                'item_id': interaction.item_id,
                'is_correct': interaction.is_correct,
                'confidence': interaction.confidence,
                'response_time_ms': interaction.response_time_ms,
                'attempts_count': interaction.attempts_count,
                'timestamp': interaction.timestamp,
                'user_aggregate': None,  # Will be populated from aggregates
                'item_aggregate': None,  # Will be populated from aggregates
                'user_interactions': [],  # Simplified for training
                'item_data': {
                    'tags': interaction.item.tags_en.split(',') if interaction.item.tags_en else [],
                    'difficulty_hint': interaction.item.difficulty_hint
                }
            })

        # Prepare features and targets
        X, y = prepare_training_data(interaction_data, confidence_threshold)

        if X.shape[0] < 20:
            return {
                "success": False,
                "error": "Insufficient valid training samples after feature extraction."
            }

        # Check class distribution
        unique_classes, class_counts = np.unique(y, return_counts=True)
        min_class_count = np.min(class_counts)

        if min_class_count < 2:
            # Try to find a suitable threshold automatically
            suitable_threshold = find_suitable_threshold(interaction_data)
            if suitable_threshold != confidence_threshold:
                # Retry with the suitable threshold
                X, y = prepare_training_data(interaction_data, suitable_threshold)
                unique_classes, class_counts = np.unique(y, return_counts=True)
                min_class_count = np.min(class_counts)

                if min_class_count < 2:
                    return {
                        "success": False,
                        "error": f"Insufficient samples for minority class even with threshold {suitable_threshold}. Minimum class count: {min_class_count}, required: 2"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Insufficient samples for minority class. Minimum class count: {min_class_count}, required: 2"
                }

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Train and calibrate model
        model, metrics = calibrate_model(X_train, y_train, X_val, y_val, calibration)

        # Calculate additional metrics
        y_val_pred = model.predict_proba(X_val)
        metrics['confident_error_rate'] = confident_error_rate(y_val, y_val_pred, confidence_threshold)

        # Save model
        os.makedirs(settings.MODELS_DIR, exist_ok=True)
        version = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = os.path.abspath(os.path.join(settings.MODELS_DIR, f"model_{version}.pkl"))
        save_model(model, model_path)

        # Create model registry entry
        params = {
            'confidence_threshold': confidence_threshold,
            'calibration': calibration,
            'bins': bins,
            'test_size': test_size,
            'n_samples': len(interaction_data),
            'n_features': X.shape[1],
            'model_path': model_path,
            'models_dir': os.path.abspath(settings.MODELS_DIR),
        }

        version = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_registry = create_model_registry(
            db=db,
            version=version,
            params_json=json.dumps(params),
            calib_type=calibration,
            ece=metrics['ece'],
            brier=metrics['brier'],
            roc_auc=metrics['roc_auc'],
            notes=f"Trained on {len(interaction_data)} interactions"
        )

        return {
            "success": True,
            "model_version": version,
            "metrics": metrics,
            "n_samples": len(interaction_data),
            "n_features": X.shape[1],
            "model_id": model_registry.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
