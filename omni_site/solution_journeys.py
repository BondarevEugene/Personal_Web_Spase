"""Verified, illustrated business-to-architecture walkthroughs.

This is an educational interactive visualization, not an execution engine.
No claims of live external integrations or empirical ROI are made.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class JourneyStep:
    code: str
    title: str
    explanation: str
    node_type: str


@dataclass(frozen=True)
class Journey:
    slug: str
    category: str
    title: str
    challenge: str
    result: str
    product_url: str
    case_url: str
    service_url: str
    facts: tuple[str, ...]
    constraints: tuple[str, ...]
    steps: tuple[JourneyStep, ...]


JOURNEYS: tuple[Journey, ...] = (
    Journey(
        slug="crm",
        category="CRM / CLIENT OPERATIONS",
        title="От сообщения клиента к управляемому заказу",
        challenge="Заявки, ТЗ, файлы и согласования разбросаны между чатами и таблицами.",
        result="Структурированный проект с этапами, версиями документов и понятной приёмкой.",
        product_url="/account/projects",
        case_url="/cases/client-workspace",
        service_url="/services/custom-crm",
        facts=("Изоляция клиентских организаций", "Версии ТЗ и согласование",
               "Замечания и повторная приёмка"),
        constraints=("Техническое согласование не заменяет электронную подпись",
                     "Платежи требуют отдельного подтверждения"),
        steps=(
            JourneyStep("01", "Заявка", "Клиент описывает задачу, роли и ожидаемый результат.", "input"),
            JourneyStep("02", "Проект", "Данные закрепляются за организацией и проектом.", "database"),
            JourneyStep("03", "Этапы", "Оператор формирует план и версии технического задания.", "workflow"),
            JourneyStep("04", "Приёмка", "Клиент принимает работу либо оставляет замечания.", "decision"),
            JourneyStep("05", "Результат", "История решений и материалов остаётся привязана к проекту.", "output"),
        ),
    ),
    Journey(
        slug="telegram",
        category="TELEGRAM / DIGITAL SERVICES",
        title="От диалога к персональному цифровому продукту",
        challenge="Человек должен пройти много шагов, загрузить материалы и не потеряться в кнопках.",
        result="Последовательный Telegram-маршрут с обработкой данных и выдачей файла.",
        product_url="/architect",
        case_url="/cases/food-porn",
        service_url="/services/telegram-bots",
        facts=("aiogram и Python-обработчики", "Сценарии выбора и ввода",
               "Цифровое меню и коллаж желаний"),
        constraints=("Видеогенерация и качество медиа требуют отдельной проверки",
                     "Промышленный хостинг не следует из самого экспорта Python"),
        steps=(
            JourneyStep("01", "Старт", "Бот определяет язык и нужный цифровой продукт.", "input"),
            JourneyStep("02", "Материалы", "Пользователь передаёт пожелания и фотографии.", "database"),
            JourneyStep("03", "Проверки", "Система проверяет необходимые параметры и этапы.", "decision"),
            JourneyStep("04", "Генерация", "Обработчики формируют графические и PDF-материалы.", "workflow"),
            JourneyStep("05", "Доставка", "Пользователь получает результат и информацию о заказе.", "output"),
        ),
    ),
    Journey(
        slug="automation",
        category="WORKFLOW / API ENGINEERING",
        title="От повторяющегося действия к контролируемому процессу",
        challenge="Операции между системами повторяются вручную, а ошибки трудно отследить.",
        result="Модель процесса с условиями, переменными, проверками и тестовой трассировкой.",
        product_url="/automation/studio",
        case_url="/cases/automation-studio",
        service_url="/services/business-automation",
        facts=("Визуальная модель workflow", "Ветвления и переменные",
               "Dry-run и трасса выполнения"),
        constraints=("Dry-run не подтверждает работу внешних API",
                     "Не все сторонние системы допускают автоматизацию"),
        steps=(
            JourneyStep("01", "Событие", "Определяем входные данные и момент запуска.", "input"),
            JourneyStep("02", "Условия", "Разделяем ветви действий по проверяемому правилу.", "decision"),
            JourneyStep("03", "Действия", "Описываем последовательность запросов и преобразований.", "workflow"),
            JourneyStep("04", "Dry-run", "Проверяем процесс на тестовых данных и изучаем трассу.", "database"),
            JourneyStep("05", "Контроль", "Фиксируем результат, исключения и границы интеграций.", "output"),
        ),
    ),
    Journey(
        slug="ai",
        category="AI / INTELLIGENT WORKFLOWS",
        title="От обращения к проверяемому AI-ответу",
        challenge="Команда вручную разбирает повторяющиеся запросы и документы, а ошибки автоматических ответов могут быть дорогостоящими.",
        result="Проектная модель ассистента с проверкой источников, ограничением доступа, подтверждением оператором и измерением качества.",
        product_url="/demo/blueprint",
        case_url="/cases/food-porn",
        service_url="/services/ai-solutions",
        facts=(
            "Python-сервис для AI-операций и обработки медиа",
            "Валидация данных и журналирование ошибок",
            "Ограничение стоимости и проверка результата",
        ),
        constraints=(
            "Демонстрация не обращается к AI API и не обрабатывает личные документы",
            "Ответы моделей могут быть неточными; критичные решения подтверждает человек",
            "Правомерность передачи данных и стоимость модели проверяются отдельно",
        ),
        steps=(
            JourneyStep("01", "Запрос", "Пользователь задаёт вопрос или передаёт разрешённый документ.", "input"),
            JourneyStep("02", "Доступ", "Проверяем разрешения, формат и допустимость передачи данных.", "decision"),
            JourneyStep("03", "Контекст", "Выбираем доступные источники и фиксируем версию данных.", "database"),
            JourneyStep("04", "AI-черновик", "Модель формирует предварительный ответ с контролем ошибок и затрат.", "workflow"),
            JourneyStep("05", "Подтверждение", "Оператор проверяет результат до отправки или выполнения действия.", "decision"),
            JourneyStep("06", "Результат", "Фиксируем согласованный ответ и диагностическую информацию.", "output"),
        ),
    )
)

BY_SLUG = {journey.slug: journey for journey in JOURNEYS}
