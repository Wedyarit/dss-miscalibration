from typing import List, Dict
from app.db.base import create_tables
from app.db.session import SessionLocal
from app.db.models import Item
from app.db.crud import create_item

QUESTIONS: List[Dict] = [
    # 1 — Statistics (p-value)
    {
        "stem_en": "In hypothesis testing, which interpretation of a p-value=0.03 is most correct?",
        "options_en": [
            "There is a 3% chance the alternative hypothesis is true.",
            "If the null hypothesis is true, observing data at least as extreme occurs with 3% probability.",
            "There is a 97% chance the result will replicate.",
            "There is a 3% chance the null hypothesis is true."
        ],
        "stem_ru": "В проверке гипотез, какое толкование p-value=0.03 наиболее корректно?",
        "options_ru": [
            "Есть 3% шанс, что альтернативная гипотеза верна.",
            "Если нулевая гипотеза верна, то наблюдать столь же экстремальные данные можно с вероятностью 3%.",
            "Есть 97% шанс, что результат повторится.",
            "Есть 3% шанс, что нулевая гипотеза верна."
        ],
        "correct": 1,
        "tags_en": ["statistics", "inference", "p-value"],
        "tags_ru": ["статистика", "выводы", "p-value"],
        "difficulty": 7.0
    },
    # 2 — Probability (Monty Hall)
    {
        "stem_en": "In the Monty Hall problem, after the host opens a goat door, what maximizes your chance to win the car?",
        "options_en": [
            "Always stay with the original choice.",
            "Always switch to the other unopened door.",
            "Randomly switch with 50% probability.",
            "It doesn't matter; chances are equal."
        ],
        "stem_ru": "В задаче Монти Холла после того как ведущий открыл дверь с козой, что максимизирует шанс выиграть машину?",
        "options_ru": [
            "Всегда оставаться при исходном выборе.",
            "Всегда переключаться на другую закрытую дверь.",
            "Случайно переключаться с вероятностью 50%.",
            "Не имеет значения; шансы равны."
        ],
        "correct": 1,
        "tags_en": ["probability", "bayes", "paradox"],
        "tags_ru": ["теория вероятностей", "Байес", "парадокс"],
        "difficulty": 6.0
    },
    # 3 — ML Calibration metric
    {
        "stem_en": "Which metric specifically quantifies the mismatch between predicted probabilities and observed frequencies?",
        "options_en": [
            "F1-score",
            "Expected Calibration Error (ECE)",
            "ROC-AUC",
            "Recall"
        ],
        "stem_ru": "Какая метрика специально измеряет несоответствие между предсказанными вероятностями и наблюдаемыми частотами?",
        "options_ru": [
            "F1-мера",
            "Ожидаемая ошибка калибровки (ECE)",
            "ROC-AUC",
            "Полнота"
        ],
        "correct": 1,
        "tags_en": ["ml", "calibration", "metrics"],
        "tags_ru": ["ML", "калибровка", "метрики"],
        "difficulty": 6.0
    },
    # 4 — Algorithms (negative edges)
    {
        "stem_en": "Which shortest-path algorithm fails to produce correct results on graphs with negative edge weights (but no negative cycles)?",
        "options_en": [
            "Bellman–Ford",
            "Dijkstra",
            "Floyd–Warshall",
            "Johnson's algorithm"
        ],
        "stem_ru": "Какой алгоритм кратчайших путей даёт неверные результаты на графах с отрицательными рёбрами (без отрицательных циклов)?",
        "options_ru": [
            "Беллмана–Форда",
            "Дейкстры",
            "Флойда–Уоршелла",
            "Алгоритм Джонсона"
        ],
        "correct": 1,
        "tags_en": ["cs", "algorithms", "graphs"],
        "tags_ru": ["информатика", "алгоритмы", "графы"],
        "difficulty": 6.5
    },
    # 5 — Data structures (range queries)
    {
        "stem_en": "Which index type is generally better for range queries on a large ordered key space?",
        "options_en": [
            "Hash index",
            "B-Tree index",
            "Bitmap index (always)",
            "Full-text index"
        ],
        "stem_ru": "Какой тип индекса обычно лучше подходит для диапазонных запросов по упорядоченному ключу?",
        "options_ru": [
            "Хеш-индекс",
            "B-Tree индекс",
            "Битмаповый индекс (всегда)",
            "Полнотекстовый индекс"
        ],
        "correct": 1,
        "tags_en": ["databases", "indexes", "systems"],
        "tags_ru": ["базы данных", "индексы", "системы"],
        "difficulty": 6.0
    },
    # 6 — Systems (ACID)
    {
        "stem_en": "Which property ensures that concurrent transactions do not interfere with each other’s intermediate states?",
        "options_en": [
            "Atomicity",
            "Consistency",
            "Isolation",
            "Durability"
        ],
        "stem_ru": "Какое свойство гарантирует, что параллельные транзакции не вмешиваются во временные состояния друг друга?",
        "options_ru": [
            "Атомарность",
            "Согласованность",
            "Изоляция",
            "Долговечность"
        ],
        "correct": 2,
        "tags_en": ["databases", "transactions", "ACID"],
        "tags_ru": ["базы данных", "транзакции", "ACID"],
        "difficulty": 5.5
    },
    # 7 — Networking (reliability)
    {
        "stem_en": "Which protocol provides reliable, ordered, and byte-stream oriented delivery?",
        "options_en": [
            "UDP",
            "TCP",
            "IP",
            "ARP"
        ],
        "stem_ru": "Какой протокол обеспечивает надёжную, упорядоченную передачу потока байтов?",
        "options_ru": [
            "UDP",
            "TCP",
            "IP",
            "ARP"
        ],
        "correct": 1,
        "tags_en": ["networking", "protocols", "transport"],
        "tags_ru": ["сети", "протоколы", "транспорт"],
        "difficulty": 5.0
    },
    # 8 — Security (hash vs encryption)
    {
        "stem_en": "Which statement best distinguishes cryptographic hashing from encryption?",
        "options_en": [
            "Hashing is reversible; encryption is not.",
            "Both are reversible transformations with a key.",
            "Encryption is reversible with a key; hashing is designed to be one-way.",
            "Both guarantee confidentiality and integrity."
        ],
        "stem_ru": "Какое утверждение лучше всего отличает криптографическое хеширование от шифрования?",
        "options_ru": [
            "Хеширование обратимо; шифрование — нет.",
            "Оба — обратимые преобразования с ключом.",
            "Шифрование обратимо с ключом; хеширование задумано как однонаправленное.",
            "Оба гарантируют конфиденциальность и целостность."
        ],
        "correct": 2,
        "tags_en": ["security", "crypto"],
        "tags_ru": ["безопасность", "крипто"],
        "difficulty": 5.5
    },
    # 9 — Psychology (confirmation bias)
    {
        "stem_en": "Which describes confirmation bias?",
        "options_en": [
            "Overestimating rare events due to vividness.",
            "Preferring information that confirms pre-existing beliefs.",
            "Attributing successes to oneself and failures to external factors.",
            "Relying on the first piece of information when making decisions."
        ],
        "stem_ru": "Что описывает предвзятость подтверждения?",
        "options_ru": [
            "Переоценка редких событий из-за их яркости.",
            "Предпочтение информации, подтверждающей изначальные убеждения.",
            "Присвоение успехов себе, а неудач — внешним факторам.",
            "Опора на первое полученное число/факт при принятии решений."
        ],
        "correct": 1,
        "tags_en": ["psychology", "biases"],
        "tags_ru": ["психология", "когнитивные искажения"],
        "difficulty": 5.0
    },
    # 10 — Physics (Rayleigh scattering)
    {
        "stem_en": "Why is the clear daytime sky predominantly blue?",
        "options_en": [
            "Mie scattering dominates shorter wavelengths.",
            "Rayleigh scattering is stronger for shorter wavelengths like blue.",
            "The ocean reflects its color into the sky.",
            "Blue light penetrates clouds more efficiently."
        ],
        "stem_ru": "Почему дневное ясное небо преимущественно голубое?",
        "options_ru": [
            "Рассеяние Ми переусиливает короткие волны.",
            "Рассеяние Рэлея сильнее для коротких волн, таких как синий.",
            "Море отражает свой цвет в небо.",
            "Синий свет эффективнее проходит сквозь облака."
        ],
        "correct": 1,
        "tags_en": ["physics", "optics"],
        "tags_ru": ["физика", "оптика"],
        "difficulty": 5.0
    },
    # 11 — Chemistry (pH concept)
    {
        "stem_en": "Aqueous solution at 25°C has [H⁺]=1×10⁻⁵ M. What is its pH?",
        "options_en": ["3", "5", "7", "9"],
        "stem_ru": "Водный раствор при 25°C имеет [H⁺]=1×10⁻⁵ М. Каков его pH?",
        "options_ru": ["3", "5", "7", "9"],
        "correct": 1,
        "tags_en": ["chemistry", "acid-base", "pH"],
        "tags_ru": ["химия", "кислотно-основное", "pH"],
        "difficulty": 5.5
    },
    # 12 — Biology (ETC location)
    {
        "stem_en": "Where is the mitochondrial electron transport chain (ETC) located in eukaryotic cells?",
        "options_en": [
            "Outer mitochondrial membrane",
            "Inner mitochondrial membrane",
            "Mitochondrial matrix",
            "Cytosol"
        ],
        "stem_ru": "Где в эукариотических клетках находится электрон-транспортная цепь митохондрий (ETC)?",
        "options_ru": [
            "Наружная мембрана митохондрий",
            "Внутренняя мембрана митохондрий",
            "Матрикс митохондрий",
            "Цитозоль"
        ],
        "correct": 1,
        "tags_en": ["biology", "cellular respiration"],
        "tags_ru": ["биология", "клеточное дыхание"],
        "difficulty": 5.5
    },
    # 13 — Economics (elasticity)
    {
        "stem_en": "If the absolute value of price elasticity of demand is greater than 1, the demand is:",
        "options_en": ["Inelastic", "Unit elastic", "Elastic", "Perfectly inelastic"],
        "stem_ru": "Если абсолютная величина ценовой эластичности спроса больше 1, то спрос:",
        "options_ru": ["Неэластичный", "Единичной эластичности", "Эластичный", "Совершенно неэластичный"],
        "correct": 2,
        "tags_en": ["economics", "microeconomics"],
        "tags_ru": ["экономика", "микроэкономика"],
        "difficulty": 5.0
    },
    # 14 — Finance (NPV)
    {
        "stem_en": "Under standard assumptions, a project with a positive Net Present Value (NPV) should be:",
        "options_en": ["Rejected", "Delayed", "Scaled down", "Accepted"],
        "stem_ru": "При стандартных предположениях проект с положительным NPV следует:",
        "options_ru": ["Отклонить", "Отложить", "Уменьшить масштаб", "Принять"],
        "correct": 3,
        "tags_en": ["finance", "valuation"],
        "tags_ru": ["финансы", "оценка"],
        "difficulty": 5.0
    },
    # 15 — Philosophy (Gettier)
    {
        "stem_en": "The Gettier problem challenges the definition of knowledge as:",
        "options_en": [
            "Belief without justification",
            "Justified true belief",
            "Pragmatic certainty",
            "Coherent web of beliefs"
        ],
        "stem_ru": "Проблема Геттиера оспаривает определение знания как:",
        "options_ru": [
            "Убеждения без обоснования",
            "Обоснованного истинного убеждения",
            "Прагматической уверенности",
            "Согласованной сети убеждений"
        ],
        "correct": 1,
        "tags_en": ["philosophy", "epistemology"],
        "tags_ru": ["философия", "эпистемология"],
        "difficulty": 6.0
    },
    # 16 — Psychology (System 1/2)
    {
        "stem_en": "According to dual-process theory, System 1 is best characterized as:",
        "options_en": [
            "Slow, effortful, rule-based",
            "Fast, automatic, heuristic",
            "Slow, statistical, Bayesian",
            "Fast, symbolic, logical"
        ],
        "stem_ru": "Согласно теории двух систем, Система 1 лучше всего характеризуется как:",
        "options_ru": [
            "Медленная, требующая усилий, правил-ориентированная",
            "Быстрая, автоматическая, эвристическая",
            "Медленная, статистическая, байесовская",
            "Быстрая, символическая, логическая"
        ],
        "correct": 1,
        "tags_en": ["psychology", "cognition"],
        "tags_ru": ["психология", "познание"],
        "difficulty": 5.0
    },
    # 17 — Medicine (sensitivity vs specificity)
    {
        "stem_en": "High sensitivity of a diagnostic test primarily reduces:",
        "options_en": [
            "False negatives",
            "False positives",
            "Type I error",
            "Prevalence"
        ],
        "stem_ru": "Высокая чувствительность диагностического теста прежде всего снижает:",
        "options_ru": [
            "Ложноотрицательные результаты",
            "Ложноположительные результаты",
            "Ошибку первого рода",
            "Заболеваемость (превалентность)"
        ],
        "correct": 0,
        "tags_en": ["medicine", "diagnostics", "statistics"],
        "tags_ru": ["медицина", "диагностика", "статистика"],
        "difficulty": 5.5
    },
    # 18 — Law (legal systems)
    {
        "stem_en": "Common law systems differ from civil law systems primarily by:",
        "options_en": [
            "Greater reliance on judicial precedents",
            "Absence of statutes",
            "Elected judges in all cases",
            "Trial by ordeal"
        ],
        "stem_ru": "Системы общего права отличаются от континентальных прежде всего:",
        "options_ru": [
            "Большей опорой на судебные прецеденты",
            "Отсутствием статутов",
            "Выборностью судей во всех случаях",
            "Судом божьим"
        ],
        "correct": 0,
        "tags_en": ["law", "legal systems"],
        "tags_ru": ["право", "правовые системы"],
        "difficulty": 5.0
    },
    # 19 — Geography (Hadley cells)
    {
        "stem_en": "Hadley cells are large-scale atmospheric circulations primarily spanning which latitudes?",
        "options_en": [
            "0°–30°",
            "30°–60°",
            "60°–90°",
            "15°–45° in each hemisphere during winter only"
        ],
        "stem_ru": "Ячейки Хэдли — это крупномасштабная атмосферная циркуляция в каких широтах прежде всего?",
        "options_ru": [
            "0°–30°",
            "30°–60°",
            "60°–90°",
            "15°–45° в каждом полушарии только зимой"
        ],
        "correct": 0,
        "tags_en": ["geography", "climate"],
        "tags_ru": ["география", "климат"],
        "difficulty": 5.0
    },
    # 20 — Astronomy (Mercury temp)
    {
        "stem_en": "Why does Mercury have extreme day–night temperature differences?",
        "options_en": [
            "Tidal heating",
            "Lack of substantial atmosphere to redistribute heat",
            "Internal geothermal activity",
            "Continuous polar storms"
        ],
        "stem_ru": "Почему на Меркурии экстремальные перепады температуры между днём и ночью?",
        "options_ru": [
            "Приливный разогрев",
            "Отсутствие значимой атмосферы для перераспределения тепла",
            "Внутренняя геотермальная активность",
            "Непрерывные полярные штормы"
        ],
        "correct": 1,
        "tags_en": ["astronomy", "planets"],
        "tags_ru": ["астрономия", "планеты"],
        "difficulty": 5.0
    },
    # 21 — Linguistics (phoneme vs morpheme)
    {
        "stem_en": "What is the primary difference between a phoneme and a morpheme?",
        "options_en": [
            "Phoneme is a unit of meaning; morpheme is a unit of sound.",
            "Both are units of meaning.",
            "Phoneme is a unit of sound; morpheme is a unit of meaning.",
            "Both are units of syntax."
        ],
        "stem_ru": "В чём основное отличие фонемы от морфемы?",
        "options_ru": [
            "Фонема — единица смысла; морфема — звука.",
            "Обе — единицы смысла.",
            "Фонема — единица звука; морфема — единица смысла.",
            "Обе — единицы синтаксиса."
        ],
        "correct": 2,
        "tags_en": ["linguistics", "semantics", "phonology"],
        "tags_ru": ["лингвистика", "семантика", "фонология"],
        "difficulty": 5.0
    },
    # 22 — Data Visualization (log scale)
    {
        "stem_en": "When is a logarithmic scale most appropriate?",
        "options_en": [
            "For data with many missing values",
            "For data spanning several orders of magnitude",
            "For normally distributed residuals",
            "For categorical comparisons"
        ],
        "stem_ru": "Когда логарифмическая шкала наиболее уместна?",
        "options_ru": [
            "Для данных с большим числом пропусков",
            "Для данных, охватывающих несколько порядков величины",
            "Для нормально распределённых остатков",
            "Для сравнения категорий"
        ],
        "correct": 1,
        "tags_en": ["data viz", "scales"],
        "tags_ru": ["визуализация данных", "шкалы"],
        "difficulty": 5.0
    },
    # 23 — Experimental design (randomization)
    {
        "stem_en": "What is the primary purpose of randomization in controlled experiments?",
        "options_en": [
            "To increase sample size",
            "To ensure balance of confounders across groups",
            "To maximize external validity",
            "To minimize measurement error"
        ],
        "stem_ru": "Какова основная цель рандомизации в контролируемых экспериментах?",
        "options_ru": [
            "Увеличить объём выборки",
            "Обеспечить баланс смешивающих факторов между группами",
            "Максимизировать внешнюю валидность",
            "Минимизировать ошибку измерения"
        ],
        "correct": 1,
        "tags_en": ["experiments", "causality", "design"],
        "tags_ru": ["эксперименты", "причинность", "дизайн"],
        "difficulty": 6.0
    },
    # 24 — Causal inference (DiD)
    {
        "stem_en": "Difference-in-differences identification relies primarily on which assumption?",
        "options_en": [
            "No measurement error",
            "Stable unit treatment value assumption",
            "Parallel trends in the absence of treatment",
            "Random assignment of treatment"
        ],
        "stem_ru": "Идентификация методом «разностей разностей» опирается прежде всего на какое предположение?",
        "options_ru": [
            "Отсутствие ошибки измерения",
            "SUTVA (стабильность эффектов)",
            "Параллельные тренды при отсутствии вмешательства",
            "Случайное назначение лечения"
        ],
        "correct": 2,
        "tags_en": ["econometrics", "causal inference"],
        "tags_ru": ["эконометрика", "причинный вывод"],
        "difficulty": 6.5
    },
    # 25 — Game theory (dominant strategy)
    {
        "stem_en": "A dominant strategy for a player is one that:",
        "options_en": [
            "Maximizes total welfare for all players",
            "Yields a higher payoff regardless of the opponent’s action",
            "Minimizes the opponent’s payoff",
            "Is a best response only to equilibrium actions"
        ],
        "stem_ru": "Доминирующая стратегия для игрока — это стратегия, которая:",
        "options_ru": [
            "Максимизирует общее благосостояние всех игроков",
            "Даёт больший выигрыш независимо от действий соперника",
            "Минимизирует выигрыш соперника",
            "Является наилучшим ответом только к равновесным действиям"
        ],
        "correct": 1,
        "tags_en": ["game theory", "strategy"],
        "tags_ru": ["теория игр", "стратегия"],
        "difficulty": 6.0
    },
    # 26 — Graph theory (Eulerian path)
    {
        "stem_en": "An undirected connected graph has an Eulerian path (but not a circuit) if and only if it has:",
        "options_en": [
            "All vertices of even degree",
            "Exactly two vertices of odd degree",
            "At least one vertex of degree one",
            "No bridges"
        ],
        "stem_ru": "У связного неориентированного графа есть эйлеров путь (но не цикл) тогда и только тогда, когда у него:",
        "options_ru": [
            "Все вершины чётной степени",
            "Ровно две вершины нечётной степени",
            "Хотя бы одна вершина степени один",
            "Нет мостов"
        ],
        "correct": 1,
        "tags_en": ["graphs", "theory"],
        "tags_ru": ["графы", "теория"],
        "difficulty": 6.0
    },
    # 27 — Software eng (algorithmic complexity nuance)
    {
        "stem_en": "Which statement about algorithmic time complexity is correct?",
        "options_en": [
            "Average-case complexity is always equal to worst-case complexity.",
            "Big-O provides an asymptotic upper bound, not an exact runtime.",
            "Amortized analysis cannot be used for dynamic arrays.",
            "Theta notation gives only a lower bound."
        ],
        "stem_ru": "Какое утверждение о временной сложности алгоритмов верно?",
        "options_ru": [
            "Средний случай всегда равен худшему.",
            "Big-O даёт асимптотическую верхнюю оценку, а не точное время.",
            "Амортизированный анализ нельзя применять к динамическим массивам.",
            "Нотация Θ задаёт только нижнюю оценку."
        ],
        "correct": 1,
        "tags_en": ["cs", "complexity"],
        "tags_ru": ["информатика", "сложность"],
        "difficulty": 5.5
    },
    # 28 — ML (ROC invariance)
    {
        "stem_en": "ROC-AUC is invariant to:",
        "options_en": [
            "Any monotonic transformation of predicted scores",
            "Calibration of predicted probabilities",
            "Class imbalance",
            "Threshold choice and prevalence simultaneously"
        ],
        "stem_ru": "ROC-AUC инвариантен к:",
        "options_ru": [
            "Любой монотонной трансформации предсказанных баллов",
            "Калибровке предсказанных вероятностей",
            "Дисбалансу классов",
            "Одновременно к порогу и распространённости"
        ],
        "correct": 0,
        "tags_en": ["ml", "metrics", "roc"],
        "tags_ru": ["ML", "метрики", "ROC"],
        "difficulty": 6.0
    },
    # 29 — Logic (implication)
    {
        "stem_en": "In classical logic, the statement 'If A then B' is false only when:",
        "options_en": [
            "A is true and B is true",
            "A is false and B is true",
            "A is true and B is false",
            "A is false and B is false"
        ],
        "stem_ru": "В классической логике высказывание «Если A, то B» ложно только когда:",
        "options_ru": [
            "A истинно и B истинно",
            "A ложно и B истинно",
            "A истинно и B ложно",
            "A ложно и B ложно"
        ],
        "correct": 2,
        "tags_en": ["logic", "reasoning"],
        "tags_ru": ["логика", "рассуждения"],
        "difficulty": 5.5
    },
    # 30 — Software systems (cache locality)
    {
        "stem_en": "Which loop transformation most commonly improves cache locality in nested loops over matrices?",
        "options_en": [
            "Loop unrolling without regard to access pattern",
            "Loop interchange to align iteration with memory layout",
            "Adding random sleeps between iterations",
            "Increasing recursion depth"
        ],
        "stem_ru": "Какое преобразование циклов чаще всего улучшает локальность кэша в вложенных циклах по матрицам?",
        "options_ru": [
            "Развёртывание циклов без учёта шаблона доступа",
            "Перестановка циклов для согласования обхода с расположением в памяти",
            "Случайные паузы между итерациями",
            "Увеличение глубины рекурсии"
        ],
        "correct": 1,
        "tags_en": ["systems", "performance", "compilers"],
        "tags_ru": ["системы", "производительность", "компиляторы"],
        "difficulty": 6.5
    },
]

def seed_questions() -> Dict[str, int]:
    create_tables()  # safe to call; creates tables if missing
    db = SessionLocal()
    created = 0
    skipped = 0
    try:
        existing_stems = {
            stem for (stem,) in db.query(Item.stem_en).all() if stem
        }
        for q in QUESTIONS:
            if q["stem_en"] in existing_stems:
                skipped += 1
                continue
            create_item(
                db=db,
                stem_en=q["stem_en"],
                options_en=q["options_en"],
                stem_ru=q["stem_ru"],
                options_ru=q["options_ru"],
                correct_option=q["correct"],
                tags_en=q["tags_en"],
                tags_ru=q["tags_ru"],
                difficulty_hint=q["difficulty"],
            )
            created += 1
        return {"created": created, "skipped": skipped, "total": len(QUESTIONS)}
    finally:
        db.close()

if __name__ == "__main__":
    result = seed_questions()
    print(
        f"Seed bilingual questions done. "
        f"Created: {result['created']}, Skipped (duplicates): {result['skipped']}, Total in script: {result['total']}"
    )
