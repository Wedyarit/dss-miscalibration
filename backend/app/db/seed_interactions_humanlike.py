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
Human-like interaction seeder.

Идеи реализма:
- Разные "персоны" студентов: базовая способность, специализация по тегам, калибровочная предвзятость (+/-),
  хронотип, склонность к скорости/аккуратности, склонность к пропускам confidence.
- Вероятность правильности ~ sigmoid(ability - difficulty + доменные скиллы + серия - усталость + шум)
- Уверенность ~ p_correct + личный bias + доменный bias + шум; подрезается в [0,1]; иногда отсутствует.
- Время ответа логнормально и коррелирует с уверенностью, сложностью и усталостью (speed-accuracy tradeoff).
- Повторения вопросов между сессиями (обучение): лёгкий рост способности при успехе, лёгкое падение при ошибке.
- Обновление агрегатов и Elo так же, как в runtime эндпоинте /sessions/{id}/answer.

Параметры можно крутить в CONFIG.
"""


# =========================
# Конфигурация
# =========================
class CONFIG:
    NUM_STUDENTS = 30                  # студентов добавим/дополняем до этого числа
    SESSIONS_PER_STUDENT = (5, 9)      # диапазон числа сессий
    QUESTIONS_PER_SESSION = (10, 18)   # диапазон числа вопросов в сессии
    SELF_CONFIDENCE_SHARE = 0.7        # доля сессий в режиме self_confidence
    CONF_MISS_PROB_STANDARD = 0.7      # вероятность, что confidence отсутствует в standard
    REPETITION_PROB = 0.25             # шанс «повторить» уже виденный вопрос через другие сессии
    BASE_DATE_DAYS = 28                # симулируем поведение за последние X дней
    RANDOM_SEED = 42                   # для воспроизводимости; можно поставить None

    # масштабирование сложностей/способностей к латентной шкале [-3, 3] (логитная)
    DIFF_SCALE = 1.8

    # эффекты
    STREAK_BONUS = 0.18               # бонус к способности за текущую «серийность» (cap 4)
    FATIGUE_PER_Q = 0.06              # усталость растёт с номером вопроса в сессии
    LEARNING_STEP_CORR = 0.08         # рост латентной способности при верном ответе
    LEARNING_STEP_WRONG = 0.05        # падение при ошибке
    LEARNING_CAP = 3.0

    # отклонения и шумы
    PERSON_ABILITY_STD = 0.8
    DOMAIN_SKILL_STD = 0.55
    BIAS_CONF_MEAN_STD = 0.15         # средний сдвиг калибровки по человеку
    BIAS_DOMAIN_STD = 0.10            # доменный сдвиг калибровки
    NOISE_P = 0.12                    # шум к вероятность успеха (логит-добавка)
    NOISE_CONF = 0.12                 # шум к уверенности
    NOISE_TIME = 0.25                 # шум к времени (логнормальный множитель)

    # время ответа (мс)
    RT_BASE = 2400
    RT_PER_DIFF = 420                 # на ед. сложности
    RT_CONF_FAST = 0.72               # множитель, если уверенность высокая
    RT_CONF_SLOW = 1.28               # множитель, если уверенность низкая
    RT_FATIGUE = 0.06                 # множитель за каждый шаг усталости

    # пороги уверенности
    HI_CONF = 0.8
    LO_CONF = 0.3

    # хронотипы: бонус/штраф к "эффективности" (логитное смещение)
    CHRONO_BONUS = {
        "lark": { "morning": +0.25, "afternoon": +0.05, "evening": -0.10, "night": -0.20 },
        "owl":  { "morning": -0.15, "afternoon": -0.05, "evening": +0.15, "night": +0.25 },
        "neutral": { "morning": 0.0, "afternoon": 0.0, "evening": 0.0, "night": -0.05 },
    }


# =========================
# Вспомогательные штуки
# =========================
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def difficulty_to_latent(diff_hint: Optional[float]) -> float:
    # diff_hint (0..10) -> [-3..+3] примерно
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


@dataclass
class Persona:
    user_id: int
    base_ability: float
    chronotype: str
    conf_bias_mean: float
    conf_missing_prob: float
    speed_accuracy: float  # >0 — быстрее, но чуть хуже точность
    domain_skill: Dict[str, float]
    domain_conf_bias: Dict[str, float]

    latent_ability_runtime: float = 0.0  # будет обновляться в ходе «обучения»
    seen_items: List[int] = None

    def reset_runtime(self):
        self.latent_ability_runtime = self.base_ability
        self.seen_items = []


def build_personas(db, students: List[User], items: List[Item]) -> Dict[int, Persona]:
    rng = np.random.default_rng(CONFIG.RANDOM_SEED)
    # выделим список всех тегов, встречающихся в вопросах
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
        conf_missing_prob = rng.uniform(0.55, 0.85)  # в standard-сессиях
        speed_accuracy = float(rng.normal(0.0, 0.5))

        # доменные скиллы и калибровочные смещения
        domain_skill = {t: float(rng.normal(0.0, CONFIG.DOMAIN_SKILL_STD)) for t in tag_universe}
        # небольшая склонность к пере-/недо-уверенности в отдельных доменах
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
    # выбираем случайный день за последние BASE_DATE_DAYS,
    # время подстраиваем под хронотип
    base = datetime.utcnow() - timedelta(days=int(rng.integers(1, CONFIG.BASE_DATE_DAYS + 1)))
    if chronotype == "lark":
        hour = int(rng.integers(6, 14))
    elif chronotype == "owl":
        # вечер/ночь
        hour = int(rng.integers(17, 24)) if rng.random() < 0.7 else int(rng.integers(0, 5))
    else:
        hour = int(rng.integers(10, 20))
    minute = int(rng.integers(0, 60))
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def choose_items_for_session(
        rng: np.random.Generator, items: List[Item], persona: Persona, n: int
) -> List[Item]:
    # позволяем повторения из "уже виденных" с некоторой вероятностью (обучение)
    pool = items.copy()
    chosen: List[Item] = []
    seen_ids = set(persona.seen_items or [])
    for _ in range(n):
        if seen_ids and rng.random() < CONFIG.REPETITION_PROB:
            # повторить
            rep_id = int(rng.choice(list(seen_ids)))
            it = next((x for x in items if x.id == rep_id), None)
            if it:
                chosen.append(it)
                continue
        # взять новый
        it = rng.choice(pool)
        chosen.append(it)
    return chosen


def tags_of_item(item: Item) -> List[str]:
    return [t.strip() for t in (item.tags_en or "").split(",") if t.strip()]


def domain_adjustment(persona: Persona, item: Item) -> float:
    tags = tags_of_item(item)
    if not tags:
        return 0.0
    # усредним вклад доменных скиллов
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
    Возвращает (is_correct, confidence, response_time_ms)
    """
    # базовая сложность
    diff_lat = difficulty_to_latent(item.difficulty_hint)
    # доменный скилл
    dom = domain_adjustment(persona, item)
    # усталость/серия/скорость-точность
    streak = min(q_index, 4)
    fatigue = q_index * CONFIG.FATIGUE_PER_Q

    # хронотип
    chrono = chronotype_bonus(persona.chronotype, tstamp)

    # скорость-точность: >0 => «быстрее, но чуть хуже точность»
    speed_penalty = 0.08 * persona.speed_accuracy

    # логит качества
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

    # базовая уверенность как «ощущение» успеха + личные калибровочные сдвиги
    conf = p_correct + persona.conf_bias_mean + domain_conf_bias(persona, item) + rng.normal(0.0, CONFIG.NOISE_CONF)
    conf = clamp(conf, 0.0, 1.0)

    # время ответа (мс)
    rt = CONFIG.RT_BASE + CONFIG.RT_PER_DIFF * (diff_lat + 1.5)  # немного нелинейности
    # скорость-точность: быстрые — ещё ускоряем, но чуть меньше времени => не всегда лучше
    rt *= (1.0 - 0.10 * persona.speed_accuracy)
    # эффект уверенности на время
    if conf >= CONFIG.HI_CONF:
        rt *= CONFIG.RT_CONF_FAST
    elif conf <= CONFIG.LO_CONF:
        rt *= CONFIG.RT_CONF_SLOW
    # усталость — медленнее
    rt *= (1.0 + CONFIG.RT_FATIGUE * fatigue)
    # добавим мультипликативный логнормальный шум
    rt *= float(np.exp(rng.normal(0.0, CONFIG.NOISE_TIME)))
    response_time_ms = int(clamp(rt, 600, 20000))

    # эволюция способности (обучение/разочарование)
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
                # режим сессии
                mode = "self_confidence" if rng.random() < CONFIG.SELF_CONFIDENCE_SHARE else "standard"
                db_session = create_session(db, stu.id, mode)
                total_sessions += 1

                # стартовое время
                t = sample_session_start(rng, persona.chronotype)

                n_q = int(rng.integers(CONFIG.QUESTIONS_PER_SESSION[0], CONFIG.QUESTIONS_PER_SESSION[1] + 1))
                picked = choose_items_for_session(rng, items, persona, n_q)

                # для серии
                current_streak = 0

                for q_idx, item in enumerate(picked, start=1):
                    # сдвинем время внутри сессии
                    t += timedelta(seconds=float(rng.integers(20, 90)))

                    is_correct, confidence, response_time_ms = simulate_one_interaction(
                        rng, persona, item, current_streak, t
                    )

                    # вероятный attempts_count
                    attempts_count = 1
                    if (not is_correct) and confidence is not None and confidence < 0.35 and rng.random() < 0.15:
                        attempts_count = 2

                    # в standard можем потерять confidence
                    conf_to_store: Optional[float] = confidence
                    if mode == "standard" and rng.random() < CONFIG.CONF_MISS_PROB_STANDARD:
                        conf_to_store = None

                    # выбрать опцию в соответствии с правильностью
                    options = item.options_en_json
                    try:
                        n_options = len(eval(options))  # JSON list хранится как текст
                    except Exception:
                        n_options = 4
                    if is_correct:
                        chosen_option = item.correct_option
                    else:
                        wrong = [i for i in range(n_options) if i != item.correct_option]
                        chosen_option = int(rng.choice(wrong)) if wrong else 0

                    # создаём Interaction
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

                    # перезапишем точный timestamp (create_interaction ставит utcnow)
                    try:
                        db.query(Interaction).filter(Interaction.id == inter.id).update({"timestamp": t})
                        db.commit()
                    except Exception:
                        db.rollback()

                    # обновим агрегаты и Elo (как в /sessions/{id}/answer)
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

                    # поддержим «серийность» для следующего вопроса
                    if is_correct:
                        current_streak = min(current_streak + 1, 4)
                    else:
                        current_streak = 0

                    # запоминаем «виденный» айтем
                    if item.id not in (persona.seen_items or []):
                        persona.seen_items.append(item.id)

        print(f"[OK] Human-like seeding done. Students: {len(students)}, Sessions: {total_sessions}, Interactions: {total_interactions}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
