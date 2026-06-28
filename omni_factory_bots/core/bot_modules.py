# ==============================================================================
# PROJECT: OMNIFACTORY // REGISTRY_CORE
# DESCRIPTION: Единый реестр 51 модуля, структурированный под архитектуру фабрики.
# ==============================================================================

MODULE_REGISTRY = {
    "CRM_SALES": {
        "label": "Бізнес, маркетинг та продажі",
        "modules": {
            "cart": {"label": "Автоматичні продажі (Кошик)", "code_template": "shop_logic"},
            "payment": {"label": "Приймання платежів (LiqPay/Stripe)", "code_template": "payment_logic"},
            "lead_gen": {"label": "Генерація лідів", "code_template": "lead_logic"},
            "funnel": {"label": "Автоматичні воронки", "code_template": "funnel_logic"},
            "survey": {"label": "Опитування та анкетування", "code_template": "survey_logic"},
            "loyalty": {"label": "Програми лояльності", "code_template": "loyalty_logic"}
        }
    },
    "ADMIN_MODERATION": {
        "label": "Адміністрування та автоматизація",
        "modules": {
            "antispam": {"label": "Антиспам", "code_template": "spam_filter"},
            "welcome_gate": {"label": "Вітання нових учасників", "code_template": "welcome_logic"},
            "content_planner": {"label": "Контент-планування", "code_template": "posting_logic"},
            "gsheet_export": {"label": "Експорт в Google Таблиці", "code_template": "gsheet_sync"},
            "feedback": {"label": "Зворотний зв'язок (Тикети)", "code_template": "feedback_logic"}
        }
    },
    "SUPPORT_AI": {
        "label": "Клієнтська підтримка",
        "modules": {
            "faq_base": {"label": "База знань (FAQ)", "code_template": "faq_logic"},
            "ai_chat": {"label": "Розумні відповіді (AI/ChatGPT)", "code_template": "ai_logic"},
            "live_chat": {"label": "Маршрутизація (Live Chat)", "code_template": "router_logic"}
        }
    },
    "SERVICES": {
        "label": "Особиста продуктивність",
        "modules": {
            "reminder": {"label": "Нагадування", "code_template": "reminder_logic"},
            "booking": {"label": "Бронювання та запис", "code_template": "booking_logic"},
            "converter": {"label": "Конвертери файлів", "code_template": "conv_logic"},
            "parser": {"label": "Парсинг та моніторинг", "code_template": "parser_logic"},
            "tracking": {"label": "Трекінг посилок", "code_template": "tracking_logic"}
        }
    },
    "MEDIA_GAMIFICATION": {
        "label": "Розваги та медіа",
        "modules": {
            "quest_game": {"label": "Текстові квести", "code_template": "game_logic"},
            "media_dl": {"label": "Завантаження медіа", "code_template": "dl_logic"},
            "dating": {"label": "Знайомства (Дейтинг)", "code_template": "dating_logic"},
            "ai_gen": {"label": "Генерація контенту (AI)", "code_template": "gen_logic"}
        }
    }
}