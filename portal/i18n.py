"""Server-rendered client workspace translations; no browser JS dependencies.

RU is the source locale; UA/EN are explicit dictionaries. Unknown keys retain
the RU source, never silently invent a machine translation at render time.
"""
from __future__ import annotations

from typing import Callable

LANGUAGES = ("uk", "ru", "en")
TRANSLATIONS: dict[str, dict[str, str]] = {
    "Обзор": {"uk": "Огляд", "en": "Overview"},
    "Заказы": {"uk": "Замовлення", "en": "Orders"},
    "Уведомления": {"uk": "Сповіщення", "en": "Notifications"},
    "Поддержка": {"uk": "Підтримка", "en": "Support"},
    "Финансы": {"uk": "Фінанси", "en": "Finances"},
    "Тарифы": {"uk": "Тарифи", "en": "Plans"},
    "Мои заказы": {"uk": "Мої замовлення", "en": "My orders"},
    "Мой кабинет": {"uk": "Мій кабінет", "en": "My workspace"},
    "Кабинет": {"uk": "Кабінет", "en": "Workspace"},
    "Все проекты": {"uk": "Усі проєкти", "en": "All projects"},
    "Все заказы": {"uk": "Усі замовлення", "en": "All orders"},
    "Тарифы и счета": {"uk": "Тарифи та рахунки", "en": "Plans and invoices"},
    "Graph Studio": {"uk": "Graph Studio", "en": "Graph Studio"},
    "Automation Studio": {"uk": "Automation Studio", "en": "Automation Studio"},
    "Рабочий кабинет": {"uk": "Робочий кабінет", "en": "Workspace dashboard"},
    "Сейчас требует внимания": {"uk": "Потребує уваги зараз", "en": "Requires attention"},
    "Фактические данные вашей организации": {"uk": "Фактичні дані вашої організації", "en": "Actual data for your organization"},
    "Проектов на приёмке": {"uk": "Проєктів на прийманні", "en": "Projects awaiting acceptance"},
    "Проектов с истёкшим сроком": {"uk": "Проєктів із простроченим терміном", "en": "Overdue projects"},
    "Непрочитанных событий": {"uk": "Непрочитаних подій", "en": "Unread events"},
    "Проверьте результаты и подтвердите готовые работы": {"uk": "Перевірте результати та підтвердьте готові роботи", "en": "Review and accept completed work"},
    "Включая проекты, которые ещё не завершены": {"uk": "Зокрема проєкти, які ще не завершено", "en": "Includes unfinished projects"},
    "Обновления по вашим проектам и документам": {"uk": "Оновлення ваших проєктів і документів", "en": "Updates to your projects and documents"},
    "Заказы в работе": {"uk": "Замовлення в роботі", "en": "Orders in progress"},
    "Сохранённые черновики": {"uk": "Збережені чернетки", "en": "Saved drafts"},
    "СХЕМЫ БОТОВ": {"uk": "СХЕМИ БОТІВ", "en": "BOT SCHEMAS"},
    "АВТОМАТИЗАЦИИ": {"uk": "АВТОМАТИЗАЦІЇ", "en": "AUTOMATIONS"},
    "ОТКРЫТЫЕ ОБРАЩЕНИЯ": {"uk": "ВІДКРИТІ ЗВЕРНЕННЯ", "en": "OPEN REQUESTS"},
    "ВСЕ ОБРАЩЕНИЯ": {"uk": "УСІ ЗВЕРНЕННЯ", "en": "ALL REQUESTS"},
    "ТЕКУЩИЙ ПЛАН": {"uk": "ПОТОЧНИЙ ТАРИФ", "en": "CURRENT PLAN"},
    "НОВЫЕ УВЕДОМЛЕНИЯ": {"uk": "НОВІ СПОВІЩЕННЯ", "en": "NEW NOTIFICATIONS"},
    "ОПЛАЧЕН ДО": {"uk": "СПЛАЧЕНО ДО", "en": "PAID THROUGH"},
    "ДОСТУП": {"uk": "ДОСТУП", "en": "ACCESS"},
    "ТЕКУЩИЙ УРОВЕНЬ": {"uk": "ПОТОЧНИЙ РІВЕНЬ", "en": "CURRENT LEVEL"},
    "Ожидает оплаты": {"uk": "Очікує оплати", "en": "Awaiting payment"},
    "Оплачен": {"uk": "Оплачено", "en": "Paid"},
    "Черновик": {"uk": "Чернетка", "en": "Draft"},
    "Отменён": {"uk": "Скасовано", "en": "Cancelled"},
    "Срок истёк": {"uk": "Термін минув", "en": "Expired"},
    "Возврат": {"uk": "Повернення", "en": "Refund"},
    "Новый запрос": {"uk": "Новий запит", "en": "New request"},
    "Планирование": {"uk": "Планування", "en": "Planning"},
    "В разработке": {"uk": "У розробці", "en": "In development"},
    "На приёмке": {"uk": "На прийманні", "en": "Awaiting acceptance"},
    "Ожидает приёмки": {"uk": "Очікує приймання", "en": "Awaiting acceptance"},
    "Принят": {"uk": "Прийнято", "en": "Accepted"},
    "Принят клиентом": {"uk": "Прийнято клієнтом", "en": "Accepted by client"},
    "Приостановлен": {"uk": "Призупинено", "en": "Paused"},
    "Завершён": {"uk": "Завершено", "en": "Completed"},
    "В работе": {"uk": "У роботі", "en": "In progress"},
    "Запланирован": {"uk": "Заплановано", "en": "Planned"},
    "Техническое задание": {"uk": "Технічне завдання", "en": "Specification"},
    "Описание результата": {"uk": "Опис результату", "en": "Delivery notes"},
    "Документ проекта": {"uk": "Документ проєкту", "en": "Project document"},
    "Проекты на заказ": {"uk": "Замовлені проєкти", "en": "Commissioned projects"},
    "Ваши обращения": {"uk": "Ваші звернення", "en": "Your requests"},
    "Настройки аккаунта": {"uk": "Налаштування облікового запису", "en": "Account settings"},
    "Подписка и платежи": {"uk": "Підписка та платежі", "en": "Subscription and payments"},
    "Мои инструменты и сохранённые проекты": {"uk": "Мої інструменти та збережені проєкти", "en": "My tools and saved projects"},
    "НА ЭТОЙ СТРАНИЦЕ": {"uk": "НА ЦІЙ СТОРІНЦІ", "en": "ON THIS PAGE"},
    "Мои проекты": {"uk": "Мої проєкти", "en": "My projects"},
    "Профиль": {"uk": "Профіль", "en": "Profile"},
    "Создать заявку": {"uk": "Створити звернення", "en": "Create support request"},
    "Новый заказ": {"uk": "Нове замовлення", "en": "New order"},
    "Финансовый центр": {"uk": "Фінансовий центр", "en": "Finance center"},
    "Счета и подписка": {"uk": "Рахунки та підписка", "en": "Invoices and subscription"},
    "Новый запрос": {"uk": "Новий запит", "en": "New request"},
    "Заказы и разработка": {"uk": "Замовлення та розробка", "en": "Orders and development"},
    "Название проекта": {"uk": "Назва проєкту", "en": "Project title"},
    "Техническая задача": {"uk": "Технічне завдання", "en": "Project brief"},
    "Отправить запрос": {"uk": "Надіслати запит", "en": "Submit request"},
    "Этапы работы": {"uk": "Етапи роботи", "en": "Work milestones"},
    "История проекта": {"uk": "Історія проєкту", "en": "Project history"},
    "Документы и согласования": {"uk": "Документи та погодження", "en": "Documents and approvals"},
    "Файлы проекта": {"uk": "Файли проєкту", "en": "Project files"},
    "Добавить файл проекта": {"uk": "Додати файл проєкту", "en": "Add project file"},
    "Загрузить файл": {"uk": "Завантажити файл", "en": "Upload file"},
    "Скачать": {"uk": "Завантажити", "en": "Download"},
    "Приёмка результата": {"uk": "Приймання результату", "en": "Delivery acceptance"},
    "Подтвердить приёмку": {"uk": "Підтвердити приймання", "en": "Accept delivery"},
    "Согласовать эту версию": {"uk": "Погодити цю версію", "en": "Approve this version"},
    "Версия": {"uk": "Версія", "en": "Version"},
    "Согласовано": {"uk": "Погоджено", "en": "Approved"},
    "Не согласовано": {"uk": "Не погоджено", "en": "Not approved"},
    "Последние события": {"uk": "Останні події", "en": "Recent events"},
    "Прочитано": {"uk": "Прочитано", "en": "Read"},
    "Новое": {"uk": "Нове", "en": "New"},
    "Открыть проект": {"uk": "Відкрити проєкт", "en": "Open project"},
    "Месяц": {"uk": "Місяць", "en": "Month"},
    "Показать": {"uk": "Показати", "en": "Show"},
    "CSV за месяц": {"uk": "CSV за місяць", "en": "Monthly CSV"},
    "Счета": {"uk": "Рахунки", "en": "Invoices"},
    "Подтверждённые операции": {"uk": "Підтверджені операції", "en": "Verified transactions"},
    "Только verified": {"uk": "Лише перевірені", "en": "Verified only"},
    "Тарифы и подписка": {"uk": "Тарифи та підписка", "en": "Plans and subscription"},
    "План подписки": {"uk": "Тарифний план", "en": "Subscription plan"},
    "История счетов организации": {"uk": "Історія рахунків організації", "en": "Organization invoice history"},
    "Почта": {"uk": "Пошта", "en": "Email"},
    "Имя": {"uk": "Ім’я", "en": "Name"},
    "Язык интерфейса": {"uk": "Мова інтерфейсу", "en": "Interface language"},
    "Часовой пояс": {"uk": "Часовий пояс", "en": "Time zone"},
    "Сохранить изменения": {"uk": "Зберегти зміни", "en": "Save changes"},
    "Выйти": {"uk": "Вийти", "en": "Sign out"},
    "Русский": {"uk": "Російська", "en": "Russian"},
    "Українська": {"uk": "Українська", "en": "Ukrainian"},
    "English": {"uk": "English", "en": "English"},
}


def normalize_language(value: object) -> str:
    """Accept only configured locale values; never accept template selectors."""
    return value if value in LANGUAGES else "ru"


def translator(language: str) -> Callable[[str], str]:
    selected = normalize_language(language)

    def translate(source: str) -> str:
        return TRANSLATIONS.get(source, {}).get(selected, source)

    return translate
