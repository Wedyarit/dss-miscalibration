export const translations = {
  en: {
    // Navigation
    nav: {
      studentTest: 'Student Test',
      instructorDashboard: 'Dashboard',
      adminQuestions: 'Admin Questions',
      adminDatasets: 'Admin Datasets',
    },

    // Student Test
    studentTest: {
      title: 'Student Test',
      subtitle: 'Take a test and see real-time miscalibration predictions',
      modeSelection: {
        title: 'Test Mode',
        standard: 'Standard',
        selfConfidence: 'Self-Confidence',
        standardDescription: 'Confidence reporting is not available',
        selfConfidenceDescription: 'Confidence reporting is required for calibration data',
        readyToStart: 'Ready to start?',
        startTest: 'Start Test',
        starting: 'Starting...',
      },
      session: {
        sessionNumber: 'Session #{id}',
        questions: 'Questions: {count}',
      },
      feedback: {
        title: 'Answer Feedback',
        correct: 'Correct',
        incorrect: 'Incorrect',
        nextQuestion: 'Next Question',
        finishTest: 'Finish Test',
      },
      confidence: {
        veryLow: 'Very Low',
        low: 'Low',
        medium: 'Medium',
        high: 'High',
        veryHigh: 'Very High',
        selectConfidence: 'Select your confidence level',
      },
      submitAnswer: 'Submit Answer',
      confirmAnswer: 'Confirm Answer',
      testCompleted: {
        title: 'Congratulations! 🎉',
        message: 'You have completed all available questions!',
        finishButton: 'Finish Test',
      },
      questionTitle: 'Question {id}',
      risk: {
        risk: 'Risk',
        highRisk: '⚠️ High probability of confident error - please review your answer',
        lowRisk: '✅ Low risk - you can proceed with confidence',
        model: 'Model',
        returnToQuestion: 'Return to Question',
        continue: 'Continue',
      },
    },

    // Common
    common: {
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      continue: 'Continue',
    },

    // Header
    header: {
      title: 'DSS Miscalibration',
      studentTest: 'Student Test',
      instructorDashboard: 'Instructor Dashboard',
      adminQuestions: 'Admin Questions',
      adminDatasets: 'Admin Datasets',
    },

    // Footer
    footer: {
      description: 'DSS Miscalibration Prediction System - Educational Demo',
    },

    // Home page
    home: {
      title: 'DSS Miscalibration Prediction System',
      subtitle: 'A Decision Support System for predicting miscalibration in learning environments',
      aboutTitle: 'About This System',
      aboutDescription:
        'This system helps identify "confident errors" where learners are highly confident but incorrect. This is crucial for personalized learning interventions, adaptive testing strategies, and instructor analytics.',
      keyFeatures: 'Key Features:',
      useCases: 'Use Cases:',
      studentTestDescription: 'Take tests in standard or self-confidence mode',
      instructorDescription: 'View analytics, reliability diagrams, and problematic questions',
      adminQuestionsDescription: 'Manage question bank, create new questions, and view analytics',
      adminDatasetsDescription: 'Seed database, train models, and export data for analysis',
      features: [
        'Real-time confidence assessment',
        'ML-powered risk prediction',
        'Calibration metrics (ECE, Brier Score)',
        'Reliability diagrams',
        'Question difficulty analysis',
      ],
      useCasesList: [
        'Adaptive learning systems',
        'Test calibration',
        'Instructor feedback',
        'Self-awareness training',
        'Educational research',
      ],
      startTestButton: 'Start Test',
      viewDashboardButton: 'View Dashboard',
      manageQuestionsButton: 'Manage Questions',
      manageDataButton: 'Manage Data',
    },

    // Instructor Dashboard
    instructor: {
      title: 'Instructor Dashboard',
      subtitle: 'View analytics, reliability diagrams, and problematic questions',
      overview: 'Overview',
      reliability: 'Reliability Diagram',
      reliabilityDescription:
        'Shows the relationship between predicted confidence and actual accuracy',
      problematicItems: 'Problematic Items',
      refreshData: 'Refresh Data',
      tableHeaders: {
        question: 'Question',
        tags: 'Tags',
        confidentErrorRate: 'Confident Error Rate',
        interactions: 'Interactions',
        avgConfidence: 'Avg Confidence',
        avgAccuracy: 'Avg Accuracy',
      },
      metrics: {
        ece: 'Expected Calibration Error',
        brier: 'Brier Score',
        rocAuc: 'ROC AUC',
        confidentErrorRate: 'Confident Error Rate',
        lowerIsBetter: 'Lower is better',
        higherIsBetter: 'Higher is better',
      },
      modelInfo: {
        title: 'Model Information',
        totalInteractions: 'Total Interactions',
        withConfidence: 'With Confidence',
        confidenceRate: 'Confidence Rate',
        lastUpdated: 'Last Updated',
      },
      reliabilityChart: {
        title: 'Reliability Diagram',
        description: 'Shows the relationship between predicted confidence and actual accuracy',
        modelVersion: 'Model Version',
        confidence: 'Confidence',
        accuracy: 'Accuracy',
        perfectCalibration: 'Perfect Calibration',
        confidenceRange: 'Confidence Range',
        legendBlue: 'Blue bars: Average confidence in each bin',
        legendRed: 'Red line: Actual accuracy in each bin',
        legendGreen: 'Green dashed line: Perfect calibration',
      },
      table: {
        question: 'Question',
        tags: 'Tags',
        confidentErrorRate: 'Confident Error Rate',
        interactions: 'Interactions',
        avgConfidence: 'Avg Confidence',
        avgAccuracy: 'Avg Accuracy',
      },
      noData: {
        message: 'No data available. Students need to take tests first.',
        startTest: 'Start Test',
      },
      error: {
        loadFailed: 'Failed to load dashboard data',
        noData: 'No data available',
        networkError: 'Network error. Please check server connection.',
      },
      actions: {
        retry: 'Retry',
      },
    },

    // Admin Questions
    adminQuestions: {
      title: 'Admin Questions',
      subtitle: 'Manage question bank, create new questions, and view analytics',
      createNew: 'Create New Question',
      questionBank: 'Question Bank',
      analytics: 'Question Analytics',
      form: {
        questionText: 'Question Text',
        questionTextEn: 'Question Text (English)',
        questionTextRu: 'Question Text (Russian)',
        options: 'Answer Options',
        optionsEn: 'Answer Options (English)',
        optionsRu: 'Answer Options (Russian)',
        correctAnswer: 'Correct Answer',
        tags: 'Tags (comma-separated)',
        tagsEn: 'Tags (English)',
        tagsRu: 'Tags (Russian)',
        difficulty: 'Difficulty Hint (1-10)',
        submit: 'Create Question',
        cancel: 'Cancel',
        addOption: 'Add Option',
        removeOption: 'Remove',
      },
      table: {
        id: 'ID',
        question: 'Question',
        tags: 'Tags',
        difficulty: 'Difficulty',
        actions: 'Actions',
        correct: 'Correct',
      },
      actions: {
        create: 'Create Question',
        edit: 'Edit',
        delete: 'Delete',
        refresh: 'Refresh',
      },
      placeholders: {
        questionText: 'Enter the question text...',
        option: 'Option {number}',
        tags: 'math, algebra, easy',
        difficulty: '5.0',
      },
      noQuestions: 'No questions found. Create your first question above.',
    },

    // Admin Datasets
    adminDatasets: {
      title: 'Admin Datasets',
      subtitle: 'Seed database, train models, and export data for analysis',
      seedDatabase: 'Seed Database',
      trainModel: 'Train Model',
      exportData: 'Export Data',
      modelStatus: 'Model Status',
      currentStatus: 'Current System Status',
      actions: {
        seed: 'Seed Database',
        train: 'Train Model',
        export: 'Export Data',
      },
      config: {
        confidenceThreshold: 'Confidence Threshold',
        calibration: 'Calibration Method',
        bins: 'Number of Bins',
        testSize: 'Test Set Size',
        thresholdDescription: '(threshold for confident errors)',
        testSizeDescription: 'for testing',
      },
      status: {
        seeding: 'Seeding database...',
        training: 'Training model...',
        exporting: 'Exporting data...',
        success: 'Operation completed successfully',
        error: 'Operation failed',
      },
      descriptions: {
        seed: 'Populate the database with demo questions and synthetic interaction data for testing and training.',
        train: 'Train the miscalibration prediction model with different calibration methods.',
        export: 'Export interaction data for offline analysis and research.',
      },
      labels: {
        totalInteractions: 'Total Interactions',
        allInteractions: 'All recorded interactions',
        withConfidence: 'With Confidence',
        confidenceInteractions: 'Interactions with confidence scores',
        modelVersion: 'Model Version',
        latestModel: 'Latest trained model',
        confidentErrorRate: 'Confident Error Rate',
        errorRate: 'Rate of confident errors',
      },
      warnings: {
        needMoreData:
          'Need at least 50 interactions with confidence scores to train a model. Seed the database first or have students take tests in self-confidence mode.',
      },
      seedResult: {
        success: 'Seeding Complete!',
        failed: 'Seeding Failed',
        usersCreated: 'Users created',
        questionsCreated: 'Questions created',
        questionsWithRussian: 'Questions with Russian',
        sessionsCreated: 'Sessions created',
        interactionsCreated: 'Interactions created',
        purposeFixed: 'Purpose fixed',
        calibrationSessions: 'Calibration sessions',
        realSessions: 'Real sessions',
      },
    },

    // Questions
    questions: {
      sampleQuestions: [
        {
          stem: 'What is the capital of France?',
          options: ['London', 'Berlin', 'Paris', 'Madrid'],
          correct_option: 2,
          tags: ['geography', 'gk'],
        },
        {
          stem: 'What is 2 + 2?',
          options: ['3', '4', '5', '6'],
          correct_option: 1,
          tags: ['math'],
        },
        {
          stem: 'Which programming language is known for its use in web development?',
          options: ['Python', 'JavaScript', 'C++', 'Java'],
          correct_option: 1,
          tags: ['cs', 'programming'],
        },
      ],
      multilingualQuestions: [
        {
          id: 1,
          en: {
            stem: 'What is the capital of France?',
            options: ['London', 'Berlin', 'Paris', 'Madrid'],
            correct_option: 2,
            tags: ['geography', 'gk'],
          },
          ru: {
            stem: 'Какой город является столицей Франции?',
            options: ['Лондон', 'Берлин', 'Париж', 'Мадрид'],
            correct_option: 2,
            tags: ['география', 'общие знания'],
          },
        },
        {
          id: 2,
          en: {
            stem: 'What is 2 + 2?',
            options: ['3', '4', '5', '6'],
            correct_option: 1,
            tags: ['math'],
          },
          ru: {
            stem: 'Сколько будет 2 + 2?',
            options: ['3', '4', '5', '6'],
            correct_option: 1,
            tags: ['математика'],
          },
        },
        {
          id: 3,
          en: {
            stem: 'Which programming language is known for its use in web development?',
            options: ['Python', 'JavaScript', 'C++', 'Java'],
            correct_option: 1,
            tags: ['cs', 'programming'],
          },
          ru: {
            stem: 'Какой язык программирования известен своим использованием в веб-разработке?',
            options: ['Python', 'JavaScript', 'C++', 'Java'],
            correct_option: 1,
            tags: ['информатика', 'программирование'],
          },
        },
      ],
    },
  },

  ru: {
    // Navigation
    nav: {
      studentTest: 'Студенческий тест',
      instructorDashboard: 'Дашборд преподавателя',
      adminQuestions: 'Управление вопросами',
      adminDatasets: 'Управление данными',
    },

    // Student Test
    studentTest: {
      title: 'Студенческий тест',
      subtitle: 'Пройдите тест и посмотрите предсказания рассогласования в реальном времени',
      modeSelection: {
        title: 'Режим тестирования',
        standard: 'Стандартный',
        selfConfidence: 'Самооценка уверенности',
        standardDescription: 'Оценка уверенности недоступна',
        selfConfidenceDescription: 'Оценка уверенности обязательна для данных калибровки',
        readyToStart: 'Готовы начать?',
        startTest: 'Начать тест',
        starting: 'Запуск...',
      },
      session: {
        sessionNumber: 'Сессия #{id}',
        questions: 'Вопросов: {count}',
      },
      feedback: {
        title: 'Обратная связь по ответу',
        correct: 'Правильно',
        incorrect: 'Неправильно',
        nextQuestion: 'Следующий вопрос',
        finishTest: 'Завершить тест',
      },
      confidence: {
        veryLow: 'Очень низкая',
        low: 'Низкая',
        medium: 'Средняя',
        high: 'Высокая',
        veryHigh: 'Очень высокая',
        selectConfidence: 'Выберите уровень уверенности',
      },
      submitAnswer: 'Отправить ответ',
      confirmAnswer: 'Подтвердить ответ',
      testCompleted: {
        title: 'Поздравляем! 🎉',
        message: 'Вы завершили все доступные вопросы!',
        finishButton: 'Завершить тест',
      },
      questionTitle: 'Вопрос {id}',
      risk: {
        risk: 'Риск',
        highRisk: '⚠️ Высокая вероятность уверенной ошибки - проверьте свой ответ',
        lowRisk: '✅ Низкий риск - можете продолжать с уверенностью',
        model: 'Модель',
        returnToQuestion: 'Вернуться к вопросу',
        continue: 'Продолжить',
      },
    },

    // Common
    common: {
      loading: 'Загрузка...',
      error: 'Ошибка',
      success: 'Успешно',
      continue: 'Продолжить',
    },

    // Header
    header: {
      title: 'DSS',
      studentTest: 'Студенческий тест',
      instructorDashboard: 'Дашборд преподавателя',
      adminQuestions: 'Управление вопросами',
      adminDatasets: 'Управление данными',
    },

    // Footer
    footer: {
      description: 'Система прогнозирования рассогласования DSS',
    },

    // Home page
    home: {
      title: 'Система прогнозирования рассогласования DSS',
      subtitle:
        'Система поддержки принятия решений для прогнозирования рассогласования в образовательных средах',
      aboutTitle: 'О системе',
      aboutDescription:
        'Эта система помогает выявлять "уверенные ошибки", когда учащиеся очень уверены в своих ответах, но отвечают неправильно. Это критически важно для персонализированных образовательных вмешательств, адаптивных стратегий тестирования и аналитики преподавателей.',
      keyFeatures: 'Ключевые возможности:',
      useCases: 'Области применения:',
      studentTestDescription: 'Тестирование в стандартном режиме или с самооценкой уверенности',
      instructorDescription: 'Просмотр аналитики, диаграмм надежности и проблемных вопросов',
      adminQuestionsDescription:
        'Управление банком вопросов, создание новых вопросов и просмотр аналитики',
      adminDatasetsDescription:
        'Заполнение базы данных, обучение моделей и экспорт данных для анализа',
      features: [
        'Оценка уверенности в реальном времени',
        'Предсказание риска на основе ИИ',
        'Метрики калибровки (ECE, Brier Score)',
        'Диаграммы надежности',
        'Анализ сложности вопросов',
      ],
      useCasesList: [
        'Адаптивные образовательные системы',
        'Калибровка тестов',
        'Обратная связь преподавателей',
        'Тренировка самосознания',
        'Образовательные исследования',
      ],
      startTestButton: 'Начать тест',
      viewDashboardButton: 'Дашборд',
      manageQuestionsButton: 'Вопросы',
      manageDataButton: 'Данные',
    },

    // Instructor Dashboard
    instructor: {
      title: 'Дашборд преподавателя',
      subtitle: 'Просмотр аналитики, диаграмм надежности и проблемных вопросов',
      overview: 'Обзор',
      reliability: 'Диаграмма надежности',
      reliabilityDescription:
        'Показывает связь между предсказанной уверенностью и фактической точностью',
      problematicItems: 'Проблемные вопросы',
      refreshData: 'Обновить данные',
      tableHeaders: {
        question: 'Вопрос',
        tags: 'Теги',
        confidentErrorRate: 'Частота уверенных ошибок',
        interactions: 'Взаимодействия',
        avgConfidence: 'Средняя уверенность',
        avgAccuracy: 'Средняя точность',
      },
      metrics: {
        ece: 'Ожидаемая ошибка калибровки',
        brier: 'Оценка Брайера',
        rocAuc: 'ROC AUC',
        confidentErrorRate: 'Частота уверенных ошибок',
        lowerIsBetter: 'Чем меньше, тем лучше',
        higherIsBetter: 'Чем больше, тем лучше',
      },
      modelInfo: {
        title: 'Информация о модели',
        totalInteractions: 'Всего взаимодействий',
        withConfidence: 'С уверенностью',
        confidenceRate: 'Частота уверенности',
        lastUpdated: 'Последнее обновление',
      },
      reliabilityChart: {
        title: 'Диаграмма надежности',
        description: 'Показывает связь между предсказанной уверенностью и фактической точностью',
        modelVersion: 'Версия модели',
        confidence: 'Уверенность',
        accuracy: 'Точность',
        perfectCalibration: 'Идеальная калибровка',
        confidenceRange: 'Диапазон уверенности',
        legendBlue: 'Синие столбцы: Средняя уверенность в каждом интервале',
        legendRed: 'Красная линия: Фактическая точность в каждом интервале',
        legendGreen: 'Зеленая пунктирная линия: Идеальная калибровка',
      },
      table: {
        question: 'Вопрос',
        tags: 'Теги',
        confidentErrorRate: 'Частота уверенных ошибок',
        interactions: 'Взаимодействия',
        avgConfidence: 'Средняя уверенность',
        avgAccuracy: 'Средняя точность',
      },
      noData: {
        message: 'Данные недоступны. Студентам нужно сначала пройти тесты.',
        startTest: 'Начать тест',
      },
      error: {
        loadFailed: 'Не удалось загрузить данные дашборда',
        noData: 'Нет данных для отображения',
        networkError: 'Ошибка сети. Проверьте подключение к серверу.',
      },
      actions: {
        retry: 'Повторить',
      },
    },

    // Admin Questions
    adminQuestions: {
      title: 'Управление вопросами',
      subtitle: 'Управление банком вопросов, создание новых вопросов и просмотр аналитики',
      createNew: 'Создать новый вопрос',
      questionBank: 'Банк вопросов',
      analytics: 'Аналитика вопросов',
      form: {
        questionText: 'Текст вопроса',
        questionTextEn: 'Текст вопроса (английский)',
        questionTextRu: 'Текст вопроса (русский)',
        options: 'Варианты ответов',
        optionsEn: 'Варианты ответов (английский)',
        optionsRu: 'Варианты ответов (русский)',
        correctAnswer: 'Правильный ответ',
        tags: 'Теги (через запятую)',
        tagsEn: 'Теги (английский)',
        tagsRu: 'Теги (русский)',
        difficulty: 'Подсказка сложности (1-10)',
        submit: 'Создать вопрос',
        cancel: 'Отмена',
        addOption: 'Добавить вариант',
        removeOption: 'Удалить',
      },
      table: {
        id: 'ID',
        question: 'Вопрос',
        tags: 'Теги',
        difficulty: 'Сложность',
        actions: 'Действия',
        correct: 'Правильно',
      },
      actions: {
        create: 'Создать вопрос',
        edit: 'Редактировать',
        delete: 'Удалить',
        refresh: 'Обновить',
      },
      placeholders: {
        questionText: 'Введите текст вопроса...',
        option: 'Вариант {number}',
        tags: 'математика, алгебра, легко',
        difficulty: '5.0',
      },
      noQuestions: 'Вопросы не найдены. Создайте первый вопрос выше.',
    },

    // Admin Datasets
    adminDatasets: {
      title: 'Управление данными',
      subtitle: 'Заполнение базы данных, обучение моделей и экспорт данных для анализа',
      seedDatabase: 'Заполнить базу данных',
      trainModel: 'Обучить модель',
      exportData: 'Экспортировать данные',
      modelStatus: 'Статус модели',
      currentStatus: 'Текущий статус системы',
      actions: {
        seed: 'Заполнить базу данных',
        train: 'Обучить модель',
        export: 'Экспортировать данные',
      },
      config: {
        confidenceThreshold: 'Порог уверенности',
        calibration: 'Метод калибровки',
        bins: 'Количество интервалов',
        testSize: 'Размер тестовой выборки',
        thresholdDescription: '(порог для уверенных ошибок)',
        testSizeDescription: 'для тестирования',
      },
      status: {
        seeding: 'Заполнение базы данных...',
        training: 'Обучение модели...',
        exporting: 'Экспорт данных...',
        success: 'Операция выполнена успешно',
        error: 'Операция не удалась',
      },
      descriptions: {
        seed: 'Заполнить базу данных демонстрационными вопросами и синтетическими данными взаимодействий для тестирования и обучения.',
        train: 'Обучить модель прогнозирования рассогласования различными методами калибровки.',
        export: 'Экспортировать данные взаимодействий для автономного анализа и исследований.',
      },
      labels: {
        totalInteractions: 'Всего взаимодействий',
        allInteractions: 'Все зарегистрированные взаимодействия',
        withConfidence: 'С уверенностью',
        confidenceInteractions: 'Взаимодействия с оценками уверенности',
        modelVersion: 'Версия модели',
        latestModel: 'Последняя обученная модель',
        confidentErrorRate: 'Частота уверенных ошибок',
        errorRate: 'Частота уверенных ошибок',
      },
      warnings: {
        needMoreData:
          'Нужно минимум 50 взаимодействий с оценками уверенности для обучения модели. Сначала заполните базу данных или попросите студентов пройти тесты в режиме самооценки.',
      },
      seedResult: {
        success: 'Заполнение завершено!',
        failed: 'Заполнение не удалось',
        usersCreated: 'Создано пользователей',
        questionsCreated: 'Создано вопросов',
        questionsWithRussian: 'Вопросов с русским языком',
        sessionsCreated: 'Создано сессий',
        interactionsCreated: 'Создано взаимодействий',
        purposeFixed: 'Исправлено purpose',
        calibrationSessions: 'Калибровочных сессий',
        realSessions: 'Реальных сессий',
      },
    },

    // Questions
    questions: {
      sampleQuestions: [
        {
          stem: 'Какой город является столицей Франции?',
          options: ['Лондон', 'Берлин', 'Париж', 'Мадрид'],
          correct_option: 2,
          tags: ['география', 'общие знания'],
        },
        {
          stem: 'Сколько будет 2 + 2?',
          options: ['3', '4', '5', '6'],
          correct_option: 1,
          tags: ['математика'],
        },
        {
          stem: 'Какой язык программирования известен своим использованием в веб-разработке?',
          options: ['Python', 'JavaScript', 'C++', 'Java'],
          correct_option: 1,
          tags: ['информатика', 'программирование'],
        },
      ],
      multilingualQuestions: [
        {
          id: 1,
          en: {
            stem: 'What is the capital of France?',
            options: ['London', 'Berlin', 'Paris', 'Madrid'],
            correct_option: 2,
            tags: ['geography', 'gk'],
          },
          ru: {
            stem: 'Какой город является столицей Франции?',
            options: ['Лондон', 'Берлин', 'Париж', 'Мадрид'],
            correct_option: 2,
            tags: ['география', 'общие знания'],
          },
        },
        {
          id: 2,
          en: {
            stem: 'What is 2 + 2?',
            options: ['3', '4', '5', '6'],
            correct_option: 1,
            tags: ['math'],
          },
          ru: {
            stem: 'Сколько будет 2 + 2?',
            options: ['3', '4', '5', '6'],
            correct_option: 1,
            tags: ['математика'],
          },
        },
        {
          id: 3,
          en: {
            stem: 'Which programming language is known for its use in web development?',
            options: ['Python', 'JavaScript', 'C++', 'Java'],
            correct_option: 1,
            tags: ['cs', 'programming'],
          },
          ru: {
            stem: 'Какой язык программирования известен своим использованием в веб-разработке?',
            options: ['Python', 'JavaScript', 'C++', 'Java'],
            correct_option: 1,
            tags: ['информатика', 'программирование'],
          },
        },
      ],
    },
  },
};

export type Language = 'en' | 'ru';
export type TranslationKey = keyof typeof translations.en;
