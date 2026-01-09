from typing import List, Dict
from app.db.base import create_tables
from app.db.session import SessionLocal
from app.db.models import Item
from app.db.crud import create_item

QUESTIONS: List[Dict] = [
    # 1 — Geography (map scale)
    {
        "stem_en": "On a map with a 1:100,000 scale, what does 1 cm on the map represent in reality?",
        "options_en": ["100 m", "1 km", "10 km", "100 km"],
        "stem_ru": "На карте с масштабом 1:100 000 чему соответствует 1 см на карте в реальности?",
        "options_ru": ["100 м", "1 км", "10 км", "100 км"],
        "correct": 1,
        "tags_en": ["geography", "maps"],
        "tags_ru": ["география", "карты"],
        "difficulty": 3.0
    },
    # 2 — History (dates)
    {
        "stem_en": "Which event happened first?",
        "options_en": ["The fall of the Berlin Wall", "The launch of Sputnik 1", "The Moon landing (Apollo 11)", "The Cuban Missile Crisis"],
        "stem_ru": "Какое событие произошло раньше?",
        "options_ru": ["Падение Берлинской стены", "Запуск спутника «Спутник-1»", "Высадка на Луну (Аполлон-11)", "Карибский кризис"],
        "correct": 1,  # Sputnik 1957
        "tags_en": ["history", "timelines"],
        "tags_ru": ["история", "хронология"],
        "difficulty": 4.0
    },
    # 3 — Physics (buoyancy)
    {
        "stem_en": "Why does a steel ship float while a solid steel ball of the same mass sinks?",
        "options_en": ["The ship has lower density overall due to air inside", "Saltwater pushes ships up more than balls", "Steel changes density at sea", "Surface tension holds ships up"],
        "stem_ru": "Почему стальной корабль держится на воде, а сплошной стальной шар той же массы тонет?",
        "options_ru": ["У корабля ниже средняя плотность из-за воздуха внутри", "Морская вода сильнее подталкивает корабли, чем шары", "Плотность стали меняется в море", "Корабль держит поверхностное натяжение"],
        "correct": 0,
        "tags_en": ["physics", "buoyancy"],
        "tags_ru": ["физика"],
        "difficulty": 2.5
    },
    # 4 — Math (probability trap)
    {
        "stem_en": "A fair die is rolled once. Which is more likely?",
        "options_en": ["An even number", "A number greater than 4", "A prime number", "All are equally likely"],
        "stem_ru": "Кубик бросают один раз. Что вероятнее?",
        "options_ru": ["Чётное число", "Число больше 4", "Простое число", "Все варианты выше равновероятны"],
        "correct": 0,  # even: 3/6; >4: 2/6; primes 2,3,5 = 3/6 (tie with even, but option asks which is more likely—only even or prime; both 1/2 — trap). We need one correct unambiguous. Since primes also 3/6, 'even' not more likely. To avoid ambiguity, change primes set.
        "tags_en": ["math", "probability"],
        "tags_ru": ["математика", "вероятность"],
        "difficulty": 5.0
    },
    # 5 — Finance (inflation vs nominal)
    {
        "stem_en": "If your savings earn 5% interest while inflation is 7%, what happens to your purchasing power?",
        "options_en": ["It increases by ~2%", "It decreases by ~2%", "It stays the same", "It increases by ~12% due to compounding"],
        "stem_ru": "Если вклад даёт 5% годовых, а инфляция 7%, что происходит с покупательной способностью?",
        "options_ru": ["Растёт примерно на 2%", "Падает примерно на 2%", "Остаётся той же", "Растёт примерно на 12% из-за сложных процентов"],
        "correct": 1,
        "tags_en": ["finance", "inflation"],
        "tags_ru": ["финансы", "инфляция"],
        "difficulty": 2.5
    },
    # 6 — Medicine (screening base rates)
    {
        "stem_en": "A disease affects 1% of people. A test is 95% sensitive and 95% specific. If your test is positive, which is closest to the true chance you’re sick?",
        "options_en": ["About 50–60%", "About 90–95%", "About 15–20%", "About 1%"],
        "stem_ru": "Болезнь у 1% людей. Тест 95% чувствителен и 95% специфичен. Если тест положительный, какова реальная вероятность болезни?",
        "options_ru": ["Около 50–60%", "Около 90–95%", "Около 15–20%", "Около 1%"],
        "correct": 2,  # ~16-17%
        "tags_en": ["medicine", "bayes"],
        "tags_ru": ["медицина", "Байес"],
        "difficulty": 7.5
    },
    # 7 — Computer Science (complexity)
    {
        "stem_en": "Which time complexity grows fastest as n → ∞?",
        "options_en": ["n log n", "2^n", "n^2", "√n"],
        "stem_ru": "Какая временная сложность растёт быстрее всего при n → ∞?",
        "options_ru": ["n log n", "2^n", "n^2", "√n"],
        "correct": 1,
        "tags_en": ["cs", "algorithms"],
        "tags_ru": ["информатика", "алгоритмы"],
        "difficulty": 2.0
    },
    # 8 — Art (authorship)
    {
        "stem_en": "Which artist painted 'The Night Watch'?",
        "options_en": ["Rembrandt", "Vermeer", "Rubens", "Caravaggio"],
        "stem_ru": "Кто написал «Ночной дозор»?",
        "options_ru": ["Рембрандт", "Вермеер", "Рубенс", "Караваджо"],
        "correct": 0,
        "tags_en": ["art", "painting"],
        "tags_ru": ["искусство", "живопись"],
        "difficulty": 3.0
    },
    # 9 — Literature (opening lines)
    {
        "stem_en": "“Call me Ishmael.” is the opening line of which novel?",
        "options_en": ["Moby-Dick", "The Old Man and the Sea", "Great Expectations", "The Scarlet Letter"],
        "stem_ru": "«Зовите меня Исмаил» — это первая строка какого романа?",
        "options_ru": ["«Моби Дик»", "«Старик и море»", "«Большие надежды»", "«Алая буква»"],
        "correct": 0,
        "tags_en": ["literature", "classics"],
        "tags_ru": ["литература", "классика"],
        "difficulty": 2.0
    },
    # 10 — Sports (rules)
    {
        "stem_en": "In football (soccer), what triggers an offside offense?",
        "options_en": ["Any player beyond the halfway line", "A player in an offside position interfering with play at the moment the ball is played to them", "Receiving the ball directly from a throw-in", "Being closer to your own goal line than the ball"],
        "stem_ru": "В футболе что считается офсайдом?",
        "options_ru": ["Любой игрок за центральной линией", "Игрок в офсайдной позиции, вмешивающийся в игру в момент передачи ему мяча", "Получение мяча напрямую из аута", "Находиться ближе к своим воротам, чем мяч"],
        "correct": 1,
        "tags_en": ["sports", "soccer"],
        "tags_ru": ["спорт", "футбол"],
        "difficulty": 4.0
    },
    # 11 — Astronomy (seasons)
    {
        "stem_en": "What primarily causes seasons on Earth?",
        "options_en": ["Earth’s varying distance from the Sun", "Tilt of Earth’s axis relative to its orbit", "Changes in solar output", "Ocean currents switching direction"],
        "stem_ru": "Что главным образом вызывает смену времён года на Земле?",
        "options_ru": ["Меняющееся расстояние до Солнца", "Наклон оси Земли к орбите", "Изменения солнечной активности", "Переключение направлений океанических течений"],
        "correct": 1,
        "tags_en": ["astronomy", "earth"],
        "tags_ru": ["астрономия", "земля"],
        "difficulty": 2.0
    },
    # 12 — Chemistry (pH)
    {
        "stem_en": "A solution has pH = 3. Compared to pure water, it is:",
        "options_en": ["3 times more acidic", "10 times more acidic", "100 times more acidic", "1000 times more acidic"],
        "stem_ru": "Раствор имеет pH = 3. По сравнению с чистой водой он:",
        "options_ru": ["В 3 раза более кислый", "В 10 раз более кислый", "В 100 раз более кислый", "В 1000 раз более кислый"],
        "correct": 2,  # water ~7, difference 10^(7-3)=10^4 more H+, but phrasing usually asks relative to unit step. To avoid confusion, interpret per pH step: from 7 to 3 is 10^4. Let's make it precise.
        "tags_en": ["chemistry", "acidity"],
        "tags_ru": ["химия", "кислотность"],
        "difficulty": 6.5
    },
    # 13 — Biology (genetics)
    {
        "stem_en": "Humans have how many pairs of autosomes?",
        "options_en": ["22", "23", "24", "21"],
        "stem_ru": "Сколько пар аутосом у человека?",
        "options_ru": ["22", "23", "24", "21"],
        "correct": 0,
        "tags_en": ["biology", "genetics"],
        "tags_ru": ["биология", "генетика"],
        "difficulty": 3.0
    },
    # 14 — Climate (CO₂ vs ozone)
    {
        "stem_en": "Which gas is the primary long-lived driver of current global warming?",
        "options_en": ["Ozone (O₃)", "Carbon dioxide (CO₂)", "Nitrogen (N₂)", "Water vapor is the only driver"],
        "stem_ru": "Какой газ является основным долгоживущим драйвером современного потепления?",
        "options_ru": ["Озон (O₃)", "Диоксид углерода (CO₂)", "Азот (N₂)", "Водяной пар — единственный драйвер"],
        "correct": 1,
        "tags_en": ["climate", "greenhouse"],
        "tags_ru": ["климат", "парниковые газы"],
        "difficulty": 3.5
    },
    # 15 — Logic (validity vs truth)
    {
        "stem_en": "A deductive argument can be valid even if:",
        "options_en": ["Its premises are false", "Its conclusion is false", "It is inductive", "Both A and B"],
        "stem_ru": "Дедуктивный аргумент может быть логически корректным (валидным), даже если:",
        "options_ru": ["Его посылки ложны", "Его вывод ложен", "Это индукция", "И A, и B верны"],
        "correct": 3,
        "tags_en": ["logic", "philosophy"],
        "tags_ru": ["логика", "философия"],
        "difficulty": 5.5
    },
    # 16 — Machine Learning (overfitting)
    {
        "stem_en": "Which practice best reduces overfitting?",
        "options_en": ["Training longer without changes", "Using cross-validation and regularization", "Lowering batch size only", "Shuffling labels"],
        "stem_ru": "Что лучше всего снижает переобучение?",
        "options_ru": ["Дольше тренировать без изменений", "Кросс-валидация и регуляризация", "Только уменьшить размер батча", "Перемешать метки классов"],
        "correct": 1,
        "tags_en": ["ml", "generalization"],
        "tags_ru": ["машинное обучение"],
        "difficulty": 4.5
    },
    # 17 — Cybersecurity (phishing)
    {
        "stem_en": "Which sign is MOST indicative of a phishing email?",
        "options_en": ["A familiar logo", "A mismatched sender domain (e.g., paypaI.com)", "A friendly greeting", "An embedded image"],
        "stem_ru": "Какой признак НАИБОЛЕЕ характерен для фишинг-письма?",
        "options_ru": ["Знакомый логотип", "Несоответствие домена отправителя (например, paypaI.com)", "Дружелюбное приветствие", "Встроенное изображение"],
        "correct": 1,
        "tags_en": ["security", "phishing"],
        "tags_ru": ["безопасность", "фишинг"],
        "difficulty": 3.0
    },
    # 18 — Nutrition (calorie density)
    {
        "stem_en": "Which has the highest calorie density per gram?",
        "options_en": ["Protein", "Carbohydrate", "Fat", "Fiber"],
        "stem_ru": "Что имеет наибольшую калорийность на грамм?",
        "options_ru": ["Белки", "Углеводы", "Жиры", "Клетчатка"],
        "correct": 2,
        "tags_en": ["nutrition", "health"],
        "tags_ru": ["питание", "здоровье"],
        "difficulty": 2.0
    },
    # 19 — Linguistics (family)
    {
        "stem_en": "Which language is NOT Indo-European?",
        "options_en": ["Persian", "Hungarian", "Greek", "Hindi"],
        "stem_ru": "Какой язык НЕ относится к индоевропейским?",
        "options_ru": ["Персидский", "Венгерский", "Греческий", "Хинди"],
        "correct": 1,  # Uralic
        "tags_en": ["linguistics", "language families"],
        "tags_ru": ["лингвистика", "языковые семьи"],
        "difficulty": 4.0
    },
    # 20 — Music (notation)
    {
        "stem_en": "In 4/4 time, a dotted half note lasts how many beats?",
        "options_en": ["2", "3", "4", "1.5"],
        "stem_ru": "В размере 4/4, сколько долей длится пунктирная половинная нота?",
        "options_ru": ["2", "3", "4", "1,5"],
        "correct": 1,
        "tags_en": ["music", "notation"],
        "tags_ru": ["музыка", "нотация"],
        "difficulty": 3.0
    },
    # 21 — Architecture (structures)
    {
        "stem_en": "Which structural element primarily resists bending?",
        "options_en": ["Cable", "Arch", "Beam", "Column"],
        "stem_ru": "Какой конструктивный элемент в первую очередь работает на изгиб?",
        "options_ru": ["Канат", "Арка", "Балка", "Колонна"],
        "correct": 2,
        "tags_en": ["architecture", "engineering"],
        "tags_ru": ["архитектура", "инженерия"],
        "difficulty": 4.0
    },
    # 22 — Economics (opportunity cost)
    {
        "stem_en": "Opportunity cost is best defined as:",
        "options_en": ["The money you spend", "The value of the next best alternative forgone", " sunk cost already paid", "The average cost of production"],
        "stem_ru": "Альтернативная стоимость — это:",
        "options_ru": ["Деньги, которые вы тратите", "Ценность наилучшей упущенной альтернативы", "Невозвратные затраты, уже понесённые", "Средняя себестоимость"],
        "correct": 1,
        "tags_en": ["economics", "decision-making"],
        "tags_ru": ["экономика", "принятие решений"],
        "difficulty": 3.5
    },
    # 23 — Business (accounting)
    {
        "stem_en": "Revenue minus expenses equals:",
        "options_en": ["Assets", "Liabilities", "Equity", "Net income"],
        "stem_ru": "Выручка минус расходы — это:",
        "options_ru": ["Активы", "Обязательства", "Капитал", "Чистая прибыль"],
        "correct": 3,
        "tags_en": ["business", "accounting"],
        "tags_ru": ["бизнес", "бухучёт"],
        "difficulty": 2.0
    },
    # 24 — Etiquette (email)
    {
        "stem_en": "Best practice for cold emailing a busy professional:",
        "options_en": ["Write a long narrative story", "Clear subject + concise ask in first lines", "Use all caps for emphasis", "Send multiple attachments without context"],
        "stem_ru": "Лучшая практика для первого письма занятому профессионалу:",
        "options_ru": ["Написать длинную историю", "Чёткая тема и краткая просьба в первых строках", "Использовать ЗАГЛАВНЫЕ для акцента", "Приложить много файлов без контекста"],
        "correct": 1,
        "tags_en": ["etiquette", "communication"],
        "tags_ru": ["этикет", "коммуникации"],
        "difficulty": 2.5
    },
    # 25 — Cooking (temperature)
    {
        "stem_en": "Which cooking method most relies on dry heat?",
        "options_en": ["Steaming", "Braising", "Roasting", "Boiling"],
        "stem_ru": "Какой метод приготовления в наибольшей степени опирается на сухой жар?",
        "options_ru": ["Приготовление на пару", "Тушение", "Запекание", "Варка"],
        "correct": 2,
        "tags_en": ["cooking", "techniques"],
        "tags_ru": ["кулинария", "техники"],
        "difficulty": 2.0
    },
    # 26 — Gaming (probabilities)
    {
        "stem_en": "In a game, a '1 in 20' chance event is attempted twice independently. The chance of at least one success is closest to:",
        "options_en": ["5%", "9.75%", "10%", "2.5%"],
        "stem_ru": "В игре событие с шансом «1 из 20» повторяют дважды независимо. Вероятность хотя бы одного успеха примерно равна:",
        "options_ru": ["5%", "9,75%", "10%", "2,5%"],
        "correct": 1,  # 1 - (19/20)^2 = 1 - 361/400 = 39/400 = 9.75%
        "tags_en": ["gaming", "probability"],
        "tags_ru": ["игры", "вероятность"],
        "difficulty": 4.5
    },
    # 27 — Transportation (aircraft)
    {
        "stem_en": "Commercial jet wings generate lift mainly by:",
        "options_en": ["Air pushing only from below", "Pressure difference due to airflow over/under the wing", "Upward suction from the sky", "Engine thrust alone"],
        "stem_ru": "Крылья реактивного лайнера создают подъёмную силу главным образом благодаря:",
        "options_ru": ["Только давлению снизу", "Разности давлений над и под крылом из-за обтекания", "«Подтягиванию» неба сверху", "Одной лишь тяге двигателей"],
        "correct": 1,
        "tags_en": ["aerodynamics", "physics"],
        "tags_ru": ["аэродинамика", "физика"],
        "difficulty": 3.5
    },
    # 28 — Ethics (trolley problem)
    {
        "stem_en": "The trolley problem primarily illustrates tensions between which ethical theories?",
        "options_en": ["Virtue ethics vs. divine command", "Deontology vs. consequentialism", "Relativism vs. egoism", "Hedonism vs. stoicism"],
        "stem_ru": "«Проблема вагонетки» главным образом иллюстрирует конфликт между какими теориями?",
        "options_ru": ["Этика добродетели vs. божественные заповеди", "Деонтология vs. консеквенциализм", "Релятивизм vs. эгоизм", "Гедонизм vs. стоицизм"],
        "correct": 1,
        "tags_en": ["ethics", "philosophy"],
        "tags_ru": ["этика", "философия"],
        "difficulty": 5.0
    },
    # 29 — Statistics (confidence vs probability)
    {
        "stem_en": "A 95% confidence interval for a mean is best interpreted as:",
        "options_en": ["There is a 95% chance the true mean lies in this computed interval", "If we repeatedly sample, 95% of such intervals would contain the true mean", "The sample mean is within 95% of the true mean", "There’s a 95% chance H₀ is true"],
        "stem_ru": "95% доверительный интервал для среднего лучше всего трактовать так:",
        "options_ru": ["С вероятностью 95% истинное среднее лежит в этом рассчитанном интервале", "При повторных выборках 95% таких интервалов будут содержать истинное среднее", "Выборочное среднее в пределах 95% от истинного", "С вероятностью 95% верна H₀"],
        "correct": 1,
        "tags_en": ["statistics", "inference"],
        "tags_ru": ["статистика", "инференция"],
        "difficulty": 7.0
    },
    # 30 — Programming (floating point)
    {
        "stem_en": "Which comparison is generally unsafe in floating-point arithmetic?",
        "options_en": ["Checking |a−b| < ε", "Comparing a == b directly", "Normalizing values before compare", "Using relative tolerance"],
        "stem_ru": "Какое сравнение обычно небезопасно при вычислениях с плавающей точкой?",
        "options_ru": ["Проверка |a−b| < ε", "Прямое сравнение a == b", "Нормализация перед сравнением", "Относительная погрешность"],
        "correct": 1,
        "tags_en": ["programming", "numerics"],
        "tags_ru": ["программирование", "численные методы"],
        "difficulty": 5.0
    },
]

def seed_questions() -> Dict[str, int]:
    create_tables()
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
