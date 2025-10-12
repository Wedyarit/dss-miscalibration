import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

def extract_user_features(user_id: int, user_aggregate: Optional[Dict], interactions: List[Dict]) -> Dict[str, float]:
    """Extract user-level features"""
    features = {}
    
    if user_aggregate:
        # EMA features (exponential moving average)
        features['ema_accuracy'] = user_aggregate.get('ema_accuracy', 0.0)
        features['ema_confidence'] = user_aggregate.get('ema_confidence', 0.0)
        features['ema_conf_gap'] = user_aggregate.get('ema_conf_gap', 0.0)
        features['elo_ability'] = user_aggregate.get('elo_ability', 1000.0)
        features['avg_time_ms'] = user_aggregate.get('avg_time_ms', 0.0)
    else:
        # Default values for new users
        features['ema_accuracy'] = 0.0
        features['ema_confidence'] = 0.0
        features['ema_conf_gap'] = 0.0
        features['elo_ability'] = 1000.0
        features['avg_time_ms'] = 0.0
    
    # Recent streak (last 5 interactions)
    if interactions:
        recent_interactions = interactions[-5:]
        streak = 0
        for interaction in reversed(recent_interactions):
            if interaction['is_correct']:
                streak += 1
            else:
                break
        features['recent_streak'] = min(streak, 5)  # Cap at 5
    else:
        features['recent_streak'] = 0
    
    return features

def extract_item_features(item_id: int, item_aggregate: Optional[Dict], item_data: Dict) -> Dict[str, float]:
    """Extract item-level features"""
    features = {}
    
    if item_aggregate:
        features['elo_difficulty'] = item_aggregate.get('elo_difficulty', 1000.0)
        features['avg_accuracy_item'] = item_aggregate.get('avg_accuracy', 0.0)
        features['avg_time_item'] = item_aggregate.get('avg_time_ms', 0.0)
    else:
        features['elo_difficulty'] = 1000.0
        features['avg_accuracy_item'] = 0.0
        features['avg_time_item'] = 0.0
    
    # Difficulty hint
    features['diff_hint'] = item_data.get('difficulty_hint', 0.0) if item_data.get('difficulty_hint') else 0.0
    
    # Tag features (one-hot encoding for main tags)
    tags = item_data.get('tags', [])
    if isinstance(tags, str):
        tags = tags.split(',') if tags else []
    elif not isinstance(tags, list):
        tags = []
    
    main_tags = ['math', 'logic', 'cs', 'reading', 'gk']
    for tag in main_tags:
        features[f'tag_{tag}'] = 1.0 if tag in tags else 0.0
    
    return features

def extract_interaction_features(interaction_data: Dict) -> Dict[str, float]:
    """Extract interaction-level features"""
    features = {}
    
    # Confidence normalized to 0-1
    confidence = interaction_data.get('confidence', 0.0)
    features['confidence_norm'] = max(0.0, min(1.0, confidence))
    
    # Log response time (handle zero/negative values)
    response_time = max(1, interaction_data.get('response_time_ms', 1000))
    features['log_response_time'] = np.log(response_time)
    
    # Attempts count
    features['attempts_count'] = float(interaction_data.get('attempts_count', 1))
    
    return features

def extract_temporal_features(timestamp: datetime) -> Dict[str, float]:
    """Extract temporal/contextual features"""
    features = {}
    
    # Hour of day (binned into 4 periods)
    hour = timestamp.hour
    if 6 <= hour < 12:
        features['hour_morning'] = 1.0
        features['hour_afternoon'] = 0.0
        features['hour_evening'] = 0.0
        features['hour_night'] = 0.0
    elif 12 <= hour < 18:
        features['hour_morning'] = 0.0
        features['hour_afternoon'] = 1.0
        features['hour_evening'] = 0.0
        features['hour_night'] = 0.0
    elif 18 <= hour < 24:
        features['hour_morning'] = 0.0
        features['hour_afternoon'] = 0.0
        features['hour_evening'] = 1.0
        features['hour_night'] = 0.0
    else:
        features['hour_morning'] = 0.0
        features['hour_afternoon'] = 0.0
        features['hour_evening'] = 0.0
        features['hour_night'] = 1.0
    
    # Day of week (one-hot encoding)
    weekday = timestamp.weekday()
    for i in range(7):
        features[f'day_{i}'] = 1.0 if weekday == i else 0.0
    
    return features

def create_feature_vector(user_features: Dict, item_features: Dict, interaction_features: Dict, temporal_features: Dict) -> np.ndarray:
    """Combine all features into a single vector"""
    
    # Define feature order for consistency
    feature_order = [
        # User features
        'ema_accuracy', 'ema_confidence', 'ema_conf_gap', 'elo_ability', 'avg_time_ms', 'recent_streak',
        # Item features
        'elo_difficulty', 'avg_accuracy_item', 'avg_time_item', 'diff_hint',
        # Tag features
        'tag_math', 'tag_logic', 'tag_cs', 'tag_reading', 'tag_gk',
        # Interaction features
        'confidence_norm', 'log_response_time', 'attempts_count',
        # Temporal features
        'hour_morning', 'hour_afternoon', 'hour_evening', 'hour_night',
        'day_0', 'day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6'
    ]
    
    feature_vector = []
    for feature_name in feature_order:
        # Get value from appropriate feature dict
        value = 0.0
        if feature_name in user_features:
            value = user_features[feature_name]
        elif feature_name in item_features:
            value = item_features[feature_name]
        elif feature_name in interaction_features:
            value = interaction_features[feature_name]
        elif feature_name in temporal_features:
            value = temporal_features[feature_name]
        
        feature_vector.append(value)
    
    return np.array(feature_vector)

def prepare_training_data(interactions: List[Dict], confidence_threshold: float = 0.7) -> tuple:
    """Prepare training data from interactions"""
    X = []
    y = []
    
    for interaction in interactions:
        # Skip interactions without confidence
        if interaction.get('confidence') is None:
            continue
        
        # Create target: confident error = (is_correct=0 & confidence>=threshold)
        is_confident_error = (not interaction['is_correct']) and (interaction['confidence'] >= confidence_threshold)
        y.append(1 if is_confident_error else 0)
        
        # Extract features (simplified for training data)
        user_features = extract_user_features(
            interaction['user_id'], 
            interaction.get('user_aggregate'), 
            interaction.get('user_interactions', [])
        )
        
        item_features = extract_item_features(
            interaction['item_id'],
            interaction.get('item_aggregate'),
            interaction.get('item_data', {})
        )
        
        interaction_features = extract_interaction_features(interaction)
        temporal_features = extract_temporal_features(interaction['timestamp'])
        
        feature_vector = create_feature_vector(user_features, item_features, interaction_features, temporal_features)
        X.append(feature_vector)
    
    return np.array(X), np.array(y)
