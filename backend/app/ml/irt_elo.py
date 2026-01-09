from typing import Tuple, Dict, Optional
import math

class EloRating:
    """Simple Elo rating system for ability and difficulty estimation"""

    def __init__(self, initial_rating: float = 1000.0, k_factor: float = 16.0):
        self.initial_rating = initial_rating
        self.k_factor = k_factor

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score for player A against player B"""
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))

    def update_rating(self, current_rating: float, expected_score: float, actual_score: float) -> float:
        """Update rating based on expected vs actual score"""
        return current_rating + self.k_factor * (actual_score - expected_score)

def update_elo_ratings(user_ability: float, item_difficulty: float,
                       is_correct: bool, k_factor: float = 16.0) -> Tuple[float, float]:
    """
    Update Elo ratings for user ability and item difficulty

    Args:
        user_ability: Current user ability rating
        item_difficulty: Current item difficulty rating
        is_correct: Whether the user answered correctly
        k_factor: Learning rate for Elo updates

    Returns:
        Tuple of (new_user_ability, new_item_difficulty)
    """
    elo = EloRating(k_factor=k_factor)

    # Expected score for user (higher ability should beat higher difficulty)
    expected_user_score = elo.expected_score(user_ability, item_difficulty)

    # Actual score (1 for correct, 0 for incorrect)
    actual_score = 1.0 if is_correct else 0.0

    # Update user ability
    new_user_ability = elo.update_rating(user_ability, expected_user_score, actual_score)

    # Update item difficulty (inverse relationship)
    # If user was correct, item becomes easier; if incorrect, item becomes harder
    expected_item_score = 1.0 - expected_user_score  # Inverse of user expectation
    actual_item_score = 1.0 - actual_score  # Inverse of user result

    new_item_difficulty = elo.update_rating(item_difficulty, expected_item_score, actual_item_score)

    return new_user_ability, new_item_difficulty

def calculate_ema(current_ema: float, new_value: float, alpha: float = 0.1) -> float:
    """Calculate exponential moving average"""
    return alpha * new_value + (1 - alpha) * current_ema

def update_user_aggregates(user_id: int, is_correct: bool, confidence: Optional[float],
                          response_time_ms: int, current_aggregates: Optional[Dict]) -> Dict:
    """Update user aggregate statistics"""

    if current_aggregates is None:
        # Initialize aggregates for new user
        aggregates = {
            'ema_accuracy': 0.0,
            'ema_confidence': 0.0,
            'ema_conf_gap': 0.0,
            'avg_time_ms': float(response_time_ms),
            'elo_ability': 1000.0
        }
    else:
        aggregates = current_aggregates.copy()

    # Update EMA accuracy
    aggregates['ema_accuracy'] = calculate_ema(aggregates['ema_accuracy'], float(is_correct))

    # Update EMA confidence (if provided)
    if confidence is not None:
        aggregates['ema_confidence'] = calculate_ema(aggregates['ema_confidence'], confidence)
        aggregates['ema_conf_gap'] = aggregates['ema_confidence'] - aggregates['ema_accuracy']

    # Update average response time (simple moving average approximation)
    alpha_time = 0.1
    aggregates['avg_time_ms'] = calculate_ema(aggregates['avg_time_ms'], float(response_time_ms), alpha_time)

    return aggregates

def update_beta_binomial_difficulty(bb_alpha: float, bb_beta: float, is_correct: bool) -> Tuple[float, float]:
    """
    Update Beta-Binomial parameters for item difficulty

    Args:
        bb_alpha: Current alpha parameter (successes + prior)
        bb_beta: Current beta parameter (failures + prior)
        is_correct: Whether the user answered correctly

    Returns:
        Tuple of (new_alpha, new_beta)
    """
    if is_correct:
        return bb_alpha + 1.0, bb_beta
    else:
        return bb_alpha, bb_beta + 1.0

def get_bb_difficulty(bb_alpha: float, bb_beta: float) -> Dict[str, float]:
    """
    Calculate difficulty metrics from Beta-Binomial parameters

    Args:
        bb_alpha: Alpha parameter
        bb_beta: Beta parameter

    Returns:
        Dict with:
        - p_error: probability of error (beta / (alpha + beta))
        - p_correct: probability of correct (alpha / (alpha + beta))
        - difficulty_logit: logit of p_error (for linear models)
        - uncertainty: variance of the posterior
    """
    total = bb_alpha + bb_beta
    if total == 0:
        # Prior: uniform
        p_error = 0.5
        p_correct = 0.5
        uncertainty = 0.25  # variance of uniform
    else:
        p_error = bb_beta / total
        p_correct = bb_alpha / total
        # Variance of Beta distribution: alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))
        uncertainty = (bb_alpha * bb_beta) / (total * total * (total + 1.0)) if total > 0 else 0.25

    # Logit transformation (with clipping to avoid log(0))
    eps = 1e-6
    p_error_clipped = max(eps, min(1.0 - eps, p_error))
    difficulty_logit = math.log(p_error_clipped / (1.0 - p_error_clipped))

    return {
        'p_error': p_error,
        'p_correct': p_correct,
        'difficulty_logit': difficulty_logit,
        'uncertainty': uncertainty
    }

def update_item_aggregates(item_id: int, is_correct: bool, confidence: Optional[float],
                          response_time_ms: int, current_aggregates: Optional[Dict]) -> Dict:
    """Update item aggregate statistics"""

    if current_aggregates is None:
        # Initialize aggregates for new item
        aggregates = {
            'avg_accuracy': 0.0,
            'avg_confidence': 0.0,
            'avg_conf_gap': 0.0,
            'avg_time_ms': float(response_time_ms),
            'elo_difficulty': 1000.0,
            'bb_alpha': 1.0,  # Laplace prior
            'bb_beta': 1.0,
            'bb_n': 0
        }
    else:
        aggregates = current_aggregates.copy()
        # Ensure BB fields exist (for backward compatibility)
        if 'bb_alpha' not in aggregates:
            aggregates['bb_alpha'] = 1.0
        if 'bb_beta' not in aggregates:
            aggregates['bb_beta'] = 1.0
        if 'bb_n' not in aggregates:
            aggregates['bb_n'] = 0

    # Update average accuracy (simple moving average approximation)
    alpha_acc = 0.1
    aggregates['avg_accuracy'] = calculate_ema(aggregates['avg_accuracy'], float(is_correct), alpha_acc)

    # Update average confidence (if provided)
    if confidence is not None:
        alpha_conf = 0.1
        aggregates['avg_confidence'] = calculate_ema(aggregates['avg_confidence'], confidence, alpha_conf)
        aggregates['avg_conf_gap'] = aggregates['avg_confidence'] - aggregates['avg_accuracy']

    # Update average response time
    alpha_time = 0.1
    aggregates['avg_time_ms'] = calculate_ema(aggregates['avg_time_ms'], float(response_time_ms), alpha_time)

    # Note: Beta-Binomial update should be done separately for real interactions only
    # This function doesn't update BB here - it's done in sessions.py based on purpose

    return aggregates
