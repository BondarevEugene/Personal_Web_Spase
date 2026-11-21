"""Public product case library built from audited first-party implementations.

Visual previews are schematic HTML diagrams, not fabricated screenshots.
No publication, live deployment, or customer outcome is implied.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    slug: str
    title: str
    category: str
    kicker: str
    summary: str
    problem: str
    approach: str
    scope: tuple[str, ...]
    limitations: tuple[str, ...]
    stack: tuple[str, ...]
    product_url: str
    action_label: str
    source_url: str
    journal_slug: str
    diagram: str


CASES: tuple[Case, ...] = (
    Case(
        slug="graph-studio",
        title="Graph Studio",
        category="Конструкторы",
        kicker="VISUAL PYTHON / TELEGRAM",
        summary="Визуальные сценарии Telegram-ботов с проверкой связей, симуляцией и экспортом отдельного Python-проекта.",
        problem="Редактор блоков должен завершаться работающим результатом, а не одной картинкой со стрелками.",
        approach="Типизированные узлы сценария, проверка переходов и экспорт в aiogram с отдельными тестами созданного файла.",
        scope=(
            "Сообщения, ввод, выбор, условия и переменные",
            "Проверка графа и пошаговая симуляция",
            "Экспорт ZIP с Python-кодом бота",
            "Отдельные тесты маршрутов экспорта",
        ),
        limitations=(
            "Экспорт сам по себе не публикует бота в облаке",
            "Для круглосуточной работы требуется отдельный процесс и хранение состояния",
        ),
        stack=("Python", "FastAPI", "Pydantic 2", "aiogram"),
        product_url="/architect",
        action_label="Открыть Graph Studio",
        source_url="https://github.com/BondarevEugene/Personal_Web_Spase",
        journal_slug="graph-studio-python-export",
        diagram="flow",
    ),
    Case(
        slug="client-workspace",
        title="Client Workspace",
        category="CRM и управление",
        kicker="PROJECT DELIVERY / BUSINESS OPS",
        summary="Кабинет с заказами, этапами, документами и согласованием результатов разработки.",
        problem="Когда ТЗ, сроки и замечания живут только в переписке, теряются версии и ответственность.",
        approach="Проектный журнал, разграничение организаций, версии ТЗ, согласование, замечания и повторная приёмка.",
        scope=(
            "Реестр заказов и этапов",
            "История редакций технического задания",
            "Приватные ограниченные по размеру вложения",
            "Замечания клиента и повторная приёмка",
        ),
        limitations=(
            "Подтверждение в кабинете не является квалифицированной электронной подписью",
            "Предварительный счёт не считается поступившим платежом",
        ),
        stack=("FastAPI", "Jinja2", "SQLAlchemy", "PostgreSQL", "Alembic"),
        product_url="/account/projects",
        action_label="Открыть кабинет",
        source_url="https://github.com/BondarevEugene/Personal_Web_Spase",
        journal_slug="client-workspace-project-acceptance",
        diagram="milestones",
    ),
    Case(
        slug="food-porn",
        title="Food_Porn",
        category="Telegram и медиа",
        kicker="PERSONALIZED DIGITAL PRODUCTS",
        summary="Telegram-продукт для персонального гастрономического меню и коллажа желаний с обработкой материалов и заказов.",
        problem="Пользователю нужно пройти несколько этапов ввода, загрузить фото и получить персональный файл без путаницы в действиях.",
        approach="Пошаговые диалоги aiogram, хранение заказов, генерация цифровых файлов и серверная проверка статусов оплаты.",
        scope=(
            "Два основных цифровых направления: меню и коллаж желаний",
            "Загрузка фотографий и пользовательского содержания",
            "Формирование графических и PDF-материалов",
            "Платёжные проверки на сервере, отдельный тестовый контур",
        ),
        limitations=(
            "Наличие платежного кода не подтверждает готовность конкретного эквайера в production",
            "Качество медиа и успешность генерации требуют тестирования на реальных заказах",
        ),
        stack=("Python", "aiogram 3", "SQLAlchemy", "PostgreSQL", "Pillow"),
        product_url="/journal/food-porn-telegram-digital-products",
        action_label="Читать технический разбор",
        source_url="https://github.com/BondarevEugene/Food_Porn",
        journal_slug="food-porn-telegram-digital-products",
        diagram="telegram",
    ),
    Case(
        slug="automation-studio",
        title="Automation Studio",
        category="Автоматизация",
        kicker="WORKFLOW / DRY-RUN",
        summary="Визуальное моделирование процессов, переменных, условий и тестовых прогонов в платформе.",
        problem="Перед запуском автоматизации необходимо видеть структуру, входы, ошибки и точки остановки.",
        approach="Редактор последовательности действий с проверкой графа и контролируемым тестовым исполнением.",
        scope=(
            "Визуальный редактор процессов",
            "Переменные, условия и переходы",
            "Тестовый dry-run и журнал результатов",
            "Отдельный рабочий маршрут редактора",
        ),
        limitations=(
            "Dry-run не означает подключение всех внешних систем",
            "Фоновые интеграции и production-исполнение требуют отдельной проверки",
        ),
        stack=("Python", "FastAPI", "JavaScript", "Workflow Graph"),
        product_url="/automation/studio",
        action_label="Открыть Automation Studio",
        source_url="https://github.com/BondarevEugene/Personal_Web_Spase",
        journal_slug="graph-studio-python-export",
        diagram="automation",
    ),
)

CASE_BY_SLUG = {item.slug: item for item in CASES}
CATEGORIES = ("Все", "Конструкторы", "CRM и управление", "Telegram и медиа", "Автоматизация")
