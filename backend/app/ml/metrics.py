import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt

def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculate Expected Calibration Error (ECE)"""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = in_bin.mean()

        if prop_in_bin > 0:
            accuracy_in_bin = y_true[in_bin].mean()
            avg_confidence_in_bin = y_prob[in_bin].mean()
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return ece

def maximum_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculate Maximum Calibration Error (MCE)"""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    mce = 0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = in_bin.mean()

        if prop_in_bin > 0:
            accuracy_in_bin = y_true[in_bin].mean()
            avg_confidence_in_bin = y_prob[in_bin].mean()
            mce = max(mce, np.abs(avg_confidence_in_bin - accuracy_in_bin))

    return mce

def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Calculate Brier Score"""
    return brier_score_loss(y_true, y_prob)

def roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Calculate ROC AUC"""
    try:
        return roc_auc_score(y_true, y_prob)
    except ValueError:
        return 0.5  # Return neutral score if only one class present

def reliability_diagram_data(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> List[Dict]:
    y_true = y_true.astype(float)
    y_prob = np.clip(y_prob, 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, n_bins + 1)

    bins = []
    alpha = 1.0; beta = 1.0  # Laplace smoothing
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        in_bin = ((y_prob >= lo) & (y_prob <= hi)) if i == 0 else ((y_prob > lo) & (y_prob <= hi))
        count = int(in_bin.sum())
        if count == 0:
            continue
        conf_avg = float(y_prob[in_bin].mean())
        k = float(y_true[in_bin].sum())                 # successes
        acc_smooth = float((k + alpha) / (count + alpha + beta))
        bins.append({
            "bin_low": float(lo),
            "bin_high": float(hi),
            "conf_avg": conf_avg,
            "acc_avg": acc_smooth,
            "count": count
        })
    return bins


def calculate_all_metrics(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict[str, float]:
    """Calculate all calibration metrics"""
    return {
        'ece': expected_calibration_error(y_true, y_prob, n_bins),
        'mce': maximum_calibration_error(y_true, y_prob, n_bins),
        'brier': brier_score(y_true, y_prob),
        'roc_auc': roc_auc(y_true, y_prob)
    }

def confident_error_rate(y_true: np.ndarray, y_prob: np.ndarray, confidence_threshold: float = 0.7) -> float:
    """Calculate confident error rate"""
    confident_mask = y_prob >= confidence_threshold
    if confident_mask.sum() == 0:
        return 0.0

    confident_errors = ((y_true == 0) & confident_mask).sum()
    confident_total = confident_mask.sum()

    return confident_errors / confident_total if confident_total > 0 else 0.0
