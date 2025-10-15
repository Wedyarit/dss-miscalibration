from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.db.base import create_tables
from app.db.session import SessionLocal
from app.db.models import User, Item, Interaction, AggregateUser, AggregateItem
from app.db.crud import (
    create_user,
    get_users_by_role,
    get_items,
    create_session,
    create_interaction,
    get_or_create_user_aggregate,
    get_or_create_item_aggregate,
    update_user_aggregate,
    update_item_aggregate,
)
from app.ml.irt_elo import update_elo_ratings, update_user_aggregates, update_item_aggregates


"""
Human-like interaction seeder (patched).

Changes vs. the original version:
- More realistic response-time tails (no hard 20s cap; increased base and variance).
- Almost no missing confidence in standard mode; confidence is quantized to UI-friendly buckets.
- Slight global positive shift for confidence (+0.03) and a bit more noise.
- Lower probability of a second attempt (attempts_count=2) to match observed user logs.
"""


# =========================
# Configuration
# =========================
class CONFIG:
    NUM_STUDENTS = 30                  # Ensure at least this many students
    SESSIONS_PER_STUDENT = (5, 9)      # Range of session counts per student
    QUESTIONS_PER_SESSION = (10, 18)   # Range of question counts per session
    SELF_CONFIDENCE_SHARE = 0.7        # Share of sessions in self_confidence mode
    # Was 0.7 in the original; that produced too many missing confidences. Keep almost all confidences.
    CONF_MISS_PROB_STANDARD = 0.05     # Probability that confidence is missing in standard mode
    REPETITION_PROB = 0.25             # Chance to repeat a previously seen item across sessions
    BASE_DATE_DAYS = 28                # Simulate behavior for the last X days
    RANDOM_SEED = 42                   # Reproducibility; set to None for full randomness

    # Map difficulty_hint (0..10) to latent scale roughly in [-3, 3] (logit space)
    DIFF_SCALE = 1.8

    # Effects
    STREAK_BONUS = 0.18               # Bonus to ability for current streak (cap 4)
    FATIGUE_PER_Q = 0.06              # Fatigue grows with the position in the session
    LEARNING_STEP_CORR = 0.08         # Ability increase after a correct answer
    LEARNING_STEP_WRONG = 0.05        # Ability decrease after a wrong answer
    LEARNING_CAP = 3.0

    # Deviations & noise
    PERSON_ABILITY_STD = 0.8
    DOMAIN_SKILL_STD = 0.55
    # Slightly wider: more inter-person calibration differences
    BIAS_CONF_MEAN_STD = 0.18         # was 0.15
    BIAS_DOMAIN_STD = 0.10            # domain-specific calibration shift
    NOISE_P = 0.12                    # logistic noise added to success probability
    NOISE_CONF = 0.15                 # was 0.12 — produce a few more extremes
    NOISE_TIME = 0.35                 # was 0.25 — longer time tails

    # Response time (ms) — increased base and sensitivity
    RT_BASE = 5000                    # was 2400
    RT_PER_DIFF = 800                 # was 420
    RT_CONF_FAST = 0.85               # was 0.72 — smaller speed-up for high confidence
    RT_CONF_SLOW = 1.35               # was 1.28 — larger slow-down for low confidence
    RT_FATIGUE = 0.08                 # was 0.06 — fatigue matters a bit more

    # Confidence thresholds
    HI_CONF = 0.8
    LO_CONF = 0.3

    # Chronotypes: logit shifts by time-of-day
    CHRONO_BONUS = {
        "lark": { "morning": +0.25, "afternoon": +0.05, "evening": -0.10, "night": -0.20 },
        "owl":  { "morning": -0.15, "afternoon": -0.05, "evening": +0.15, "night": +0.25 },
        "neutral": { "morning": 0.0, "afternoon": 0.0, "evening": 0.0, "night": -0.05 },
    }


# Discrete confidence buckets expected by the UI
CONF_BUCKETS = [0.0, 0.15, 0.2, 0.4, 0.6, 0.8, 1.0]


# =========================
# Helpers
# =========================
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def difficulty_to_latent(diff_hint: Optional[float]) -> float:
    # diff_hint (0..10) -> [-3..+3] approximately
    d = 5.0 if diff_hint is None else diff_hint
    z = (d - 5.0) / CONFIG.DIFF_SCALE
    return clamp(z, -3.0, 3.0)


def pick_period(hour: int) -> str:
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 24:
        return "evening"
    return "night"


def quantize_conf(c: float) -> float:
    """Snap confidence to the nearest value in CONF_BUCKETS."""
    best = CONF_BUCKETS[0]
    best_d = abs(c - best)
    for b in CONF_BUCKETS[1:]:
        d = abs(c - b)
        if d < best_d:
            best, best_d = b, d
    return best


@dataclass
class Persona:
    user_id: int
    base_ability: float
    chronotype: str
    conf_bias_mean: float
    conf_missing_prob: float
    speed_accuracy: float  # >0 — faster, but slightly worse accuracy
    domain_skill: Dict[str, float]
    domain_conf_bias: Dict[str, float]

    latent_ability_runtime: float = 0.0  # evolves during "learning"
    seen_items: List[int] = None

    def reset_runtime(self):
        self.latent_ability_runtime = self.base_ability
        self.seen_items = []


def build_personas(db, students: List[User], items: List[Item]) -> Dict[int, Persona]:
    rng = np.random.default_rng(CONFIG.RANDOM_SEED)
    # Enumerate all tags present in items
    tag_universe: List[str] = []
    for it in items:
        if it.tags_en:
            for t in [s.strip() for s in it.tags_en.split(",") if s.strip()]:
                if t not in tag_universe:
                    tag_universe.append(t)

    personas: Dict[int, Persona] = {}
    for u in students:
        chronotype = rng.choice(["lark", "neutral", "owl"], p=[0.35, 0.30, 0.35])
        base_ability = float(rng.normal(0.0, CONFIG.PERSON_ABILITY_STD))
        conf_bias_mean = float(rng.normal(0.0, CONFIG.BIAS_CONF_MEAN_STD))
        conf_missing_prob = rng.uniform(0.55, 0.85)  # used in standard sessions
        speed_accuracy = float(rng.normal(0.0, 0.5))

        # Domain skills and calibration shifts
        domain_skill = {t: float(rng.normal(0.0, CONFIG.DOMAIN_SKILL_STD)) for t in tag_universe}
        domain_conf_bias = {t: float(rng.normal(0.0, CONFIG.BIAS_DOMAIN_STD)) for t in tag_universe}

        p = Persona(
            user_id=u.id,
            base_ability=clamp(base_ability, -2.5, 2.5),
            chronotype=chronotype,
            conf_bias_mean=clamp(conf_bias_mean, -0.35, 0.35),
            conf_missing_prob=conf_missing_prob,
            speed_accuracy=clamp(speed_accuracy, -1.0, 1.0),
            domain_skill=domain_skill,
            domain_conf_bias=domain_conf_bias,
        )
        p.reset_runtime()
        personas[u.id] = p
    return personas


def sample_session_start(rng: np.random.Generator, chronotype: str) -> datetime:
    # Pick a random day within the last BASE_DATE_DAYS;
    # time-of-day is biased by chronotype.
    base = datetime.utcnow() - timedelta(days=int(rng.integers(1, CONFIG.BASE_DATE_DAYS + 1)))
    if chronotype == "lark":
        hour = int(rng.integers(6, 14))
    elif chronotype == "owl":
        # Evening/night
        hour = int(rng.integers(17, 24)) if rng.random() < 0.7 else int(rng.integers(0, 5))
    else:
        hour = int(rng.integers(10, 20))
    minute = int(rng.integers(0, 60))
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def choose_items_for_session(
        rng: np.random.Generator, items: List[Item], persona: Persona, n: int
) -> List[Item]:
    # Allow repeats from "already seen" with some probability (learning)
    pool = items.copy()
    chosen: List[Item] = []
    seen_ids = set(persona.seen_items or [])
    for _ in range(n):
        if seen_ids and rng.random() < CONFIG.REPETITION_PROB:
            # Repeat
            rep_id = int(rng.choice(list(seen_ids)))
            it = next((x for x in items if x.id == rep_id), None)
            if it:
                chosen.append(it)
                continue
        # Take a new item
        it = rng.choice(pool)
        chosen.append(it)
    return chosen


def tags_of_item(item: Item) -> List[str]:
    return [t.strip() for t in (item.tags_en or "").split(",") if t.strip()]


def domain_adjustment(persona: Persona, item: Item) -> float:
    tags = tags_of_item(item)
    if not tags:
        return 0.0
    # Average the domain skills across tags
    vals = [persona.domain_skill.get(t, 0.0) for t in tags]
    return float(np.mean(vals)) if vals else 0.0


def domain_conf_bias(persona: Persona, item: Item) -> float:
    tags = tags_of_item(item)
    if not tags:
        return 0.0
    vals = [persona.domain_conf_bias.get(t, 0.0) for t in tags]
    return float(np.mean(vals)) if vals else 0.0


def chronotype_bonus(chronotype: str, dt: datetime) -> float:
    period = pick_period(dt.hour)
    return CONFIG.CHRONO_BONUS.get(chronotype, {}).get(period, 0.0)


def simulate_one_interaction(
        rng: np.random.Generator,
        persona: Persona,
        item: Item,
        q_index: int,
        tstamp: datetime,
) -> Tuple[bool, Optional[float], int]:
    """
    Returns (is_correct, confidence, response_time_ms)
    """
    # Base difficulty
    diff_lat = difficulty_to_latent(item.difficulty_hint)
    # Domain skill
    dom = domain_adjustment(persona, item)
    # Fatigue/streak/speed-accuracy
    streak = min(q_index, 4)
    fatigue = q_index * CONFIG.FATIGUE_PER_Q

    # Chronotype
    chrono = chronotype_bonus(persona.chronotype, tstamp)

    # Speed-accuracy trade-off: >0 => faster but slightly worse accuracy
    speed_penalty = 0.08 * persona.speed_accuracy

    # Logit of success
    logit = (
            (persona.latent_ability_runtime + dom - diff_lat)
            + CONFIG.STREAK_BONUS * streak
            - fatigue
            + chrono
            - speed_penalty
            + rng.normal(0.0, CONFIG.NOISE_P)
    )
    p_correct = clamp(sigmoid(logit), 0.02, 0.98)
    is_correct = rng.random() < p_correct

    # Confidence: "feeling" of success + personal/domain calibration + noise
    conf = p_correct + persona.conf_bias_mean + domain_conf_bias(persona, item) + rng.normal(0.0, CONFIG.NOISE_CONF)
    # Slight global overconfidence
    conf = conf + 0.03
    conf = clamp(conf, 0.0, 1.0)
    # Quantize to UI buckets
    conf = quantize_conf(conf)

    # Response time (ms)
    rt = CONFIG.RT_BASE + CONFIG.RT_PER_DIFF * (diff_lat + 1.5)  # slight nonlinearity
    # Speed-accuracy: "fast" personas get a bit faster
    rt *= (1.0 - 0.10 * persona.speed_accuracy)
    # Confidence effect on time
    if conf >= CONFIG.HI_CONF:
        rt *= CONFIG.RT_CONF_FAST
    elif conf <= CONFIG.LO_CONF:
        rt *= CONFIG.RT_CONF_SLOW
    # Fatigue slows down
    rt *= (1.0 + CONFIG.RT_FATIGUE * fatigue)
    # Multiplicative lognormal noise
    rt *= float(np.exp(rng.normal(0.0, CONFIG.NOISE_TIME)))
    # Allow up to 60s
    response_time_ms = int(clamp(rt, 600, 60000))

    # Ability evolution (learning / discouragement)
    if is_correct:
        persona.latent_ability_runtime = clamp(
            persona.latent_ability_runtime + CONFIG.LEARNING_STEP_CORR * (1.0 - persona.latent_ability_runtime / CONFIG.LEARNING_CAP),
            -CONFIG.LEARNING_CAP, CONFIG.LEARNING_CAP
        )
    else:
        persona.latent_ability_runtime = clamp(
            persona.latent_ability_runtime - CONFIG.LEARNING_STEP_WRONG * (1.0 + persona.latent_ability_runtime / CONFIG.LEARNING_CAP),
            -CONFIG.LEARNING_CAP, CONFIG.LEARNING_CAP
        )

    return is_correct, conf, response_time_ms


def ensure_students(db, target_n: int) -> List[User]:
    students = get_users_by_role(db, "student")
    need = max(0, target_n - len(students))
    for _ in range(need):
        create_user(db, "student")
    return get_users_by_role(db, "student")


def main():
    if CONFIG.RANDOM_SEED is not None:
        random.seed(CONFIG.RANDOM_SEED)
        np.random.seed(CONFIG.RANDOM_SEED)

    create_tables()
    db = SessionLocal()

    try:
        items = get_items(db, limit=1000)
        if len(items) < 20:
            print(f"[WARN] Only {len(items)} items found. Consider seeding bilingual questions first.")
        students = ensure_students(db, CONFIG.NUM_STUDENTS)

        personas = build_personas(db, students, items)

        total_sessions = 0
        total_interactions = 0

        rng = np.random.default_rng(CONFIG.RANDOM_SEED)

        for stu in students:
            persona = personas[stu.id]
            persona.reset_runtime()

            n_sessions = int(rng.integers(CONFIG.SESSIONS_PER_STUDENT[0], CONFIG.SESSIONS_PER_STUDENT[1] + 1))
            for s_idx in range(n_sessions):
                # Session mode
                mode = "self_confidence" if rng.random() < CONFIG.SELF_CONFIDENCE_SHARE else "standard"
                db_session = create_session(db, stu.id, mode)
                total_sessions += 1

                # Session start time
                t = sample_session_start(rng, persona.chronotype)

                n_q = int(rng.integers(CONFIG.QUESTIONS_PER_SESSION[0], CONFIG.QUESTIONS_PER_SESSION[1] + 1))
                picked = choose_items_for_session(rng, items, persona, n_q)

                # For streaks
                current_streak = 0

                for q_idx, item in enumerate(picked, start=1):
                    # Advance time within the session
                    t += timedelta(seconds=float(rng.integers(20, 90)))

                    is_correct, confidence, response_time_ms = simulate_one_interaction(
                        rng, persona, item, current_streak, t
                    )

                    # attempts_count
                    attempts_count = 1
                    # Lower chance of a second attempt
                    if (not is_correct) and confidence is not None and confidence < 0.35 and rng.random() < 0.05:
                        attempts_count = 2

                    # In standard mode, confidence may be missing (now rare)
                    conf_to_store: Optional[float] = confidence
                    if mode == "standard" and rng.random() < CONFIG.CONF_MISS_PROB_STANDARD:
                        conf_to_store = None

                    # Choose option according to correctness
                    options = item.options_en_json
                    try:
                        n_options = len(eval(options))  # JSON list stored as text
                    except Exception:
                        n_options = 4
                    if is_correct:
                        chosen_option = item.correct_option
                    else:
                        wrong = [i for i in range(n_options) if i != item.correct_option]
                        chosen_option = int(rng.choice(wrong)) if wrong else 0

                    # Create Interaction
                    inter = create_interaction(
                        db=db,
                        session_id=db_session.id,
                        user_id=stu.id,
                        item_id=item.id,
                        chosen_option=chosen_option,
                        is_correct=is_correct,
                        confidence=conf_to_store,
                        response_time_ms=response_time_ms,
                        attempts_count=attempts_count,
                    )
                    total_interactions += 1

                    # Overwrite timestamp with simulated time (create_interaction uses utcnow)
                    try:
                        db.query(Interaction).filter(Interaction.id == inter.id).update({"timestamp": t})
                        db.commit()
                    except Exception:
                        db.rollback()

                    # Update aggregates and Elo (same as /sessions/{id}/answer)
                    try:
                        user_agg = get_or_create_user_aggregate(db, stu.id)
                        item_agg = get_or_create_item_aggregate(db, item.id)

                        new_user_ability, new_item_difficulty = update_elo_ratings(
                            user_agg.elo_ability, item_agg.elo_difficulty, is_correct
                        )

                        user_updates = update_user_aggregates(
                            stu.id,
                            is_correct,
                            conf_to_store,
                            response_time_ms,
                            {
                                "ema_accuracy": user_agg.ema_accuracy,
                                "ema_confidence": user_agg.ema_confidence,
                                "ema_conf_gap": user_agg.ema_conf_gap,
                                "avg_time_ms": user_agg.avg_time_ms,
                                "elo_ability": user_agg.elo_ability,
                            },
                        )
                        user_updates["elo_ability"] = new_user_ability
                        update_user_aggregate(db, stu.id, **user_updates)

                        item_updates = update_item_aggregates(
                            item.id,
                            is_correct,
                            conf_to_store,
                            response_time_ms,
                            {
                                "avg_accuracy": item_agg.avg_accuracy,
                                "avg_confidence": item_agg.avg_confidence,
                                "avg_conf_gap": item_agg.avg_conf_gap,
                                "avg_time_ms": item_agg.avg_time_ms,
                                "elo_difficulty": item_agg.elo_difficulty,
                            },
                        )
                        item_updates["elo_difficulty"] = new_item_difficulty
                        update_item_aggregate(db, item.id, **item_updates)

                    except Exception as e:
                        db.rollback()
                        print(f"[WARN] Aggregate update failed: {e}")

                    # Maintain streak for the next question
                    if is_correct:
                        current_streak = min(current_streak + 1, 4)
                    else:
                        current_streak = 0

                    # Remember seen item
                    if item.id not in (persona.seen_items or []):
                        persona.seen_items.append(item.id)

        print(f"[OK] Human-like seeding done. Students: {len(students)}, Sessions: {total_sessions}, Interactions: {total_interactions}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
