from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import os

import numpy as np
from sklearn.metrics import average_precision_score

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.crud import (
    get_interactions_for_training,
    create_model_registry,
)
from app.ml.calibrate import CalibrationWrapper, save_model
from app.ml.metrics import (
    calculate_all_metrics,
    confident_error_rate,
)
from app.ml.features import (
    extract_user_features,
    extract_item_features,
    extract_interaction_features,
    extract_temporal_features,
    create_feature_vector,
)

# ---------- helpers ----------

@dataclass
class RollingAgg:
    ema_accuracy: float = 0.0
    ema_confidence: float = 0.0
    ema_conf_gap: float = 0.0
    avg_time_ms: float = 0.0
    elo: float = 1000.0
    # для streak (последние k исходов)
    recent_corrects: List[int] = None
    # Beta-Binomial parameters for items
    bb_alpha: float = 1.0
    bb_beta: float = 1.0

    def __post_init__(self):
        if self.recent_corrects is None:
            self.recent_corrects = []

def _ema(cur: float, new_val: float, alpha: float = 0.1) -> float:
    return alpha * new_val + (1 - alpha) * cur

def _update_user_roll(ra: RollingAgg, is_correct: bool, confidence: Optional[float], rt_ms: int):
    ra.ema_accuracy = _ema(ra.ema_accuracy, float(is_correct))
    if confidence is not None:
        ra.ema_confidence = _ema(ra.ema_confidence, float(confidence))
        ra.ema_conf_gap = ra.ema_confidence - ra.ema_accuracy
    ra.avg_time_ms = _ema(ra.avg_time_ms, float(rt_ms), alpha=0.1)
    # streak
    ra.recent_corrects.append(1 if is_correct else 0)
    if len(ra.recent_corrects) > 5:
        ra.recent_corrects.pop(0)

def _streak_from_recent(recent: List[int]) -> int:
    s = 0
    for x in reversed(recent):
        if x == 1:
            s += 1
        else:
            break
    return min(s, 5)


def _effective_confidence(inter) -> Optional[float]:
    return inter.initial_confidence if inter.initial_confidence is not None else inter.confidence


def _effective_is_correct(inter) -> bool:
    if inter.initial_chosen_option is None:
        return bool(inter.is_correct)
    try:
        initial_option = int(inter.initial_chosen_option)
    except (TypeError, ValueError):
        return bool(inter.is_correct)
    if inter.item is None:
        return bool(inter.is_correct)
    return initial_option == inter.item.correct_option

def _build_training_rows(interactions, conf_thr: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Строим фичи 'как будто в онлайне':
    идём по времени, считаем роллинг-агрегаты до текущего события (чтобы не было утечки).
    """
    # сортируем по времени
    interactions = sorted(interactions, key=lambda r: r.timestamp)

    user_state: Dict[int, RollingAgg] = {}
    item_state: Dict[int, RollingAgg] = {}

    X_rows: List[np.ndarray] = []
    y_rows: List[int] = []

    for inter in interactions:
        eff_confidence = _effective_confidence(inter)
        if eff_confidence is None:
            continue
        eff_is_correct = _effective_is_correct(inter)

        uid = inter.user_id
        iid = inter.item_id

        # текущее "прошлое" состояние
        u = user_state.get(uid, RollingAgg())
        it = item_state.get(iid, RollingAgg())

        # формируем признаки строго из прошлого
        user_agg_dict = {
            "ema_accuracy": u.ema_accuracy,
            "ema_confidence": u.ema_confidence,
            "ema_conf_gap": u.ema_conf_gap,
            "elo_ability": u.elo,           # заглушка: реального elo нет, но порядок фичей сохраняем
            "avg_time_ms": u.avg_time_ms,
            "recent_streak": _streak_from_recent(u.recent_corrects),
        }

        # Use Beta-Binomial difficulty for items (as in real tests)
        item_agg_dict = {
            "bb_alpha": it.bb_alpha,
            "bb_beta": it.bb_beta,
            "elo_difficulty": it.elo,  # Legacy, kept for compatibility
            "avg_accuracy": it.ema_accuracy,
            "avg_time_ms": it.avg_time_ms,
        }

        item_data = {
            "tags": inter.item.tags_en.split(",") if inter.item and inter.item.tags_en else [],
            "difficulty_hint": inter.item.difficulty_hint if inter.item else None,
        }

        # используем уже готовые экстракторы (они сами возьмут нужные поля)
        uf = extract_user_features(inter.user_id, user_agg_dict, [])  # уже содержит recent_streak
        itf = extract_item_features(inter.item_id, item_agg_dict, item_data)
        # Build interaction features WITHOUT confidence (as in real tests)
        # This ensures model works in production where confidence may not be available
        intf = extract_interaction_features(
            {
                # Don't include confidence - model should work without it
                "response_time_ms": inter.response_time_ms,
                "attempts_count": inter.attempts_count,
            }
        )
        tf = extract_temporal_features(inter.timestamp)

        X_rows.append(create_feature_vector(uf, itf, intf, tf))

        # целевая метка: confident error
        y_rows.append(int((not eff_is_correct) and (eff_confidence >= conf_thr)))

        # теперь ОБНОВЛЯЕМ состояние "после" ответа — уже не влияет на текущие фичи
        _update_user_roll(u, eff_is_correct, eff_confidence, inter.response_time_ms)
        _update_user_roll(it, eff_is_correct, eff_confidence, inter.response_time_ms)
        # Update Beta-Binomial for item (simulating real test updates)
        if eff_is_correct:
            it.bb_alpha += 1.0
        else:
            it.bb_beta += 1.0
        user_state[uid] = u
        item_state[iid] = it

    return np.array(X_rows), np.array(y_rows)

def _time_based_split(X: np.ndarray, y: np.ndarray, ratios=(0.8, 0.2)) -> Tuple[np.ndarray, ...]:
    """Простой time-based split: первые 80% → train, остальное → val."""
    n = X.shape[0]
    cut = int(n * ratios[0])
    return X[:cut], X[cut:], y[:cut], y[cut:]

def _choose_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """
    Подбираем decision-threshold для риска по максимуму PR AUC на error-класс,
    ограничивая долю alarms (опционально можно добавить).
    Здесь оставим дефолт 0.5, а функция — задел на будущее.
    """
    return 0.5

# ---------- public API ----------

def find_suitable_threshold(interaction_data: List[Dict], min_samples_per_class: int = 2) -> float:
    """Обратная совместимость со старым API — оставим как есть (используется редко)."""
    thresholds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    for threshold in thresholds:
        filtered = [d for d in interaction_data if d.get("confidence") is not None and d.get("confidence") >= threshold]
        if len(filtered) < min_samples_per_class * 2:
            continue
        targets = [d["is_correct"] for d in filtered]
        uniq, cnts = np.unique(targets, return_counts=True)
        if np.min(cnts) >= min_samples_per_class:
            return threshold
    return 0.1

def train_model(
        confidence_threshold: float = 0.7,
        calibration: str = "platt",
        bins: int = 10,
        test_size: float = 0.2,   # не используется напрямую, оставлен для обратной совместимости API
) -> Dict:
    """
    Обучение модели риска уверенной ошибки без утечки:
    - строим фичи из "прошлого" (rolling-агрегаты на лету),
    - time-based split (первые 80% во времени → train, остальное → val),
    - логистическая регрессия с class_weight='balanced' + калибровка (Platt/Isotonic/None),
    - логируем ROC AUC / PR AUC / ECE / Brier / CER.
    """
    db = SessionLocal()
    try:
        # Get only calibration interactions (where confidence is available)
        inters = get_interactions_for_training(db, limit=10000, purpose="calibration")
        if len(inters) < 50:
            return {
                "success": False,
                "error": "Insufficient training data. Need at least 50 interactions with confidence scores."
            }

        # Формируем обучающий датасет с роллинг-агрегатами (без утечки)
        X, y = _build_training_rows(inters, confidence_threshold)
        if X.shape[0] < 50:
            return {"success": False, "error": "Too few valid samples after feature extraction."}

        # time-based split (X уже в хронологическом порядке)
        X_train, X_val, y_train, y_val = _time_based_split(X, y, ratios=(0.8, 0.2))

        # Модель с балансировкой классов
        model = CalibrationWrapper(calibration_type=calibration)
        # подменяем базовую LR с class_weight='balanced'
        from sklearn.linear_model import LogisticRegression
        model.base_model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight="balanced",
        )
        model.fit(X_train, y_train)

        # Валидация
        y_val_prob = model.predict_proba(X_val)

        # Классические калибровочные метрики для "положительного" класса (confident error)
        metrics = calculate_all_metrics(y_val, y_val_prob, n_bins=bins)
        # PR AUC по положительному классу (информативно при дисбалансе)
        pr_auc = average_precision_score(y_val, y_val_prob)
        metrics["pr_auc"] = float(pr_auc)

        # CER: как часто ошибаемся, когда модель уверена, что ошибки не будет (или наоборот)
        # В исходной постановке CER считали по confidence; здесь — по предсказанному риску.
        # Оставим оба варианта: ниже — по предсказанному риску.
        cer_val = confident_error_rate(
            y_true=(1 - y_val),           # 1 = корректно, 0 = ошибка → функция писалась под другой таргет
            y_prob=(1 - y_val_prob),      # вероятность "быть корректным"
            confidence_threshold=0.7
        )
        metrics["cer_pred_risk"] = float(cer_val)

        # для совместимости — основные поля TrainResponse
        os.makedirs(settings.MODELS_DIR, exist_ok=True)
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.abspath(os.path.join(settings.MODELS_DIR, f"model_{version}.pkl"))
        save_model(model, model_path)

        params = {
            "confidence_threshold": confidence_threshold,
            "calibration": calibration,
            "bins": bins,
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "model_path": model_path,
            "models_dir": os.path.abspath(settings.MODELS_DIR),
            "split": "time_based_80_20",
            "class_weight": "balanced",
        }

        # регистрируем модель (как и раньше)
        mr = create_model_registry(
            db=db,
            version=version,
            params_json=json.dumps(params),
            calib_type=calibration,
            ece=metrics["ece"],
            brier=metrics["brier"],
            roc_auc=metrics["roc_auc"],
            notes=f"PR AUC={metrics['pr_auc']:.3f}; CER(pred risk)={metrics['cer_pred_risk']:.3f}",
            friendly_name=f"Iteration 2 model ({calibration}, {metrics['roc_auc']:.2f} ROC-AUC)",
            is_active=True
        )

        return {
            "success": True,
            "model_version": version,
            "metrics": metrics,
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "model_id": mr.id,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()
