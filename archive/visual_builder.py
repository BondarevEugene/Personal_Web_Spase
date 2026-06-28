print(">>> [DEBUG] Загружается файл:", __file__)
# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /visual_builder.py
# VERSION: 3.5.0 (COCKPIT NO-CODE PRODUCTION STABLE)
# PART: 1 OF 3 (INITIALIZATION, STATES & INTERFACE BUFFERS)
# LAST MODIFIED: 2026-05-20
# DESCRIPTION: Визуальный No-Code конструктор "Папа Ботов" (Flet Engine).
# PURPOSE:
#   1. Полноразмерный трехсекционный интерфейс управления ИИ-агентами OmniFactory.
#   2. Инициализация глобального реактивного стейта веток Mind-Map.
#   3. Защитное предварительное объявление интерфейсных контейнеров бэкенда.
# AUTHOR: Eugene Bondarev & Gemini AI Collaborator
# STATUS: Active / Production Core Engine / UTF-8 Verified / Part 1 Ready
# ==============================================================================

import flet as ft
import asyncio
import httpx
from datetime import datetime
from services.bot_factory import MODULES_REGISTRY

API_URL = "http://127.0.0.1:8000/api/v1/deploy"


def build_papa_bots_view(page: ft.Page):
    page.title = "OmniFactory EVO // Визуальный Папа Ботов"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#09090e"
    page.padding = 12

    # --- ГЛОБАЛЬНЫЙ ВНУТРЕННИЙ СТЭЙТ КОНСТРУКТОРА ---
    selected_category = "all"
    search_query = ""
    active_step_idx = 0
    logs_loop_task = None
    selected_tab_idx = 0
    selected_module_ids = set(["welcome"])

    # Карта коммуникации бота — базовое дерево шагов сценария
    bot_dialog_tree = [
        {
            "id": "step_1",
            "title": "Старт Системы",
            "type": "CORE",
            "text": "🤖 Бот успешно сгенерирован на OmniFactory EVO!\n\nВыберите кубики автоматизации слева и настройте ветки логики:",
            "buttons": ["🎵 Скачать Медиа", "🧠 ИИ Консультант", "📋 Помощь"]
        },
        {
            "id": "step_2",
            "title": "ИИ Консультант",
            "type": "AI_AGENT",
            "text": "🧠 Запущен изолированный ИИ-агент OmniFactory.\n\nЗадайте ваш вопрос нейросети:",
            "buttons": ["↩ Назад", "💳 Оплата"]
        }
    ]

    # --- ЗАЩИТНОЕ ОБЪЯВЛЕНИЕ КОНТЕЙНЕРОВ (Ликвидация NameError версий Flet) ---
    modules_list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    phone_screen_content = ft.Column(spacing=8, expand=True)
    tree_canvas_container = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    category_tabs_container = ft.Row(spacing=5, scroll=ft.ScrollMode.ADAPTIVE)

    # Элементы живой телеметрии и логов сборочной линии Docker
    terminal_display = ft.Text(
        "[SYSTEM] Сборочная линия заведена. Ожидание конфигурации веток...\n",
        size=10, color="#00ff41", font_family="JetBrains Mono"
    )
    status_label = ft.Text("STATUS: IDLE", size=11, color="#00ffff", weight=ft.FontWeight.BOLD)
    docker_id_label = ft.Text("DOCKER: NONE", size=10, color="#71717a", weight=ft.FontWeight.BOLD)

    # Поля правого инспектора параметров текущего блока диалога
    token_input = ft.TextField(
        label="[BOT_API_TOKEN]", password=True, can_reveal_password=True,
        hint_text="Токен от @BotFather...", height=38,
        border_color="rgba(188, 19, 254, 0.4)", focused_border_color="#bc13fe",
        label_style=ft.TextStyle(color="#bc13fe", size=10, font_family="Orbitron"),
        text_style=ft.TextStyle(color="white", size=11)
    )

    node_text_input = ft.TextField(
        label="Текст текущего узла диалога / Системный промпт", multiline=True, min_lines=3, max_lines=4,
        border_color="rgba(0, 255, 255, 0.3)", focused_border_color="#00ffff",
        label_style=ft.TextStyle(color="#00ffff", size=11), text_style=ft.TextStyle(color="white", size=12),
    )

    media_url_input = ft.TextField(
        label="Медиа оболочка блока (URL картинки / GIF)",
        hint_text="https://...", height=38,
        border_color="rgba(188, 19, 254, 0.3)", focused_border_color="#bc13fe",
        label_style=ft.TextStyle(color="#71717a", size=10), text_style=ft.TextStyle(color="#00ff41", size=11)
    )
    # --- ЛОГИКА СИНХРОНИЗАЦИИ, ФИЛЬТРАЦИИ И ПОТОКОВЫХ СОБЫТИЙ ---
    # --- ВЕРСТКА: ЛЕВАЯ КОЛОНКА (Модули) ---
    left_column = ft.Container(
        content=ft.Column([
            ft.Text("MODULES_REGISTRY", size=14, weight=ft.FontWeight.BOLD, color="#bc13fe", font_family="Orbitron"),
            modules_list_container
        ], spacing=10),
        padding=10,
        bgcolor="#0b0b10",
        border_radius=6,
        border=ft.Border(
            left=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)"),
            top=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)"),
            right=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)"),
            bottom=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)")
        ),
        width=250
    )

    # --- ВЕРСТКА: ЦЕНТРАЛЬНАЯ КОЛОНКА (Канвас/Визуал) ---
    center_column = ft.Container(
        content=ft.Column([
            ft.Text("MIND_MAP_CANVAS", size=14, weight=ft.FontWeight.BOLD, color="#00ffff", font_family="Orbitron"),
            tree_canvas_container
        ], spacing=10),
        padding=15,
        bgcolor="#0b0b10",
        border_radius=6,
        border=ft.Border(
            left=ft.BorderSide(1, "rgba(0, 255, 255, 0.2)"),
            top=ft.BorderSide(1, "rgba(0, 255, 255, 0.2)"),
            right=ft.BorderSide(1, "rgba(0, 255, 255, 0.2)"),
            bottom=ft.BorderSide(1, "rgba(0, 255, 255, 0.2)")
        ),
        expand=True
    )

    # --- ВЕРСТКА: ПРАВАЯ КОЛОНКА (Инспектор) ---
    right_column = ft.Container(
        content=ft.Column([
            ft.Text("NODE_INSPECTOR", size=14, weight=ft.FontWeight.BOLD, color="#71717a", font_family="Orbitron"),
            token_input,
            node_text_input,
            media_url_input,
            phone_screen_content,
            terminal_display,
            ft.Row([status_label, docker_id_label], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                ft.ElevatedButton("COMPILE", bgcolor="#00ff41", color="black", icon="play_arrow", expand=True),
                ft.ElevatedButton("KILL", bgcolor="#ff0055", color="white", icon="dangerous")
            ], spacing=8)
        ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=10,
        bgcolor="#0b0b10",
        border_radius=6,
        border=ft.Border(
            left=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)"),
            top=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)"),
            right=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)"),
            bottom=ft.BorderSide(1, "rgba(188, 19, 254, 0.2)")
        ),
        width=310
    )

    # --- ФУНКЦИИ ОБРАБОТКИ СОБЫТИЙ ---
    def on_docker_start_click(e):
        status_label.value = "STATUS: COMPILING..."
        status_label.color = "#00ffff"
        page.update()
        # Тут логика запуска через API...

    def update_terminal(text):
        terminal_display.value += f"\n{text}"
        page.update()

    # --- ИНИЦИАЛИЗАЦИЯ ИНТЕРФЕЙСА ---
    category_tabs_container.controls = [
        ft.TextButton(c, on_click=lambda e: print(f"Filter: {c}"))
        for c in ["ALL", "AI", "CORE", "MEDIA"]
    ]

    # Сборка общего вида
    page.add(
        ft.Row([category_tabs_container], alignment=ft.MainAxisAlignment.START),
        ft.Divider(height=1, color="white10"),
        ft.Row(controls=[left_column, center_column, right_column], spacing=10, expand=True)
    )
    # --- ОПРЕДЕЛЕНИЕ КОМПОНЕНТОВ (для вставки в right_column) ---

    # 1. Phone Wrapper (имитация экрана телефона)
    phone_wrapper = ft.Container(
        content=phone_screen_content,
        height=200,
        bgcolor="#050508",
        padding=10,
        border_radius=4,
        border=ft.Border(
            left=ft.BorderSide(1, "#3f3f46"),
            top=ft.BorderSide(1, "#3f3f46"),
            right=ft.BorderSide(1, "#3f3f46"),
            bottom=ft.BorderSide(1, "#3f3f46")
        )
    )

    # 2. Terminal Box (экран логов)
    terminal_box = ft.Container(
        content=ft.Column([terminal_display], scroll=ft.ScrollMode.ADAPTIVE),
        height=150,
        bgcolor="#020204",
        padding=10,
        border_radius=4,
        border=ft.Border(
            left=ft.BorderSide(1, "#18181b"),
            top=ft.BorderSide(1, "#18181b"),
            right=ft.BorderSide(1, "#18181b"),
            bottom=ft.BorderSide(1, "#18181b")
        )
    )

    # --- ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ ---
    def on_docker_stop_click(e):
        status_label.value = "STATUS: STOPPING..."
        status_label.color = "#ff0055"
        update_terminal("[SYSTEM] Остановка процессов...")
        page.update()
        # Тут твоя логика остановки через API
        asyncio.create_task(async_stop_process())

    async def async_stop_process():
        await asyncio.sleep(1)
        status_label.value = "STATUS: IDLE"
        status_label.color = "#00ffff"
        update_terminal("[SYSTEM] Процессы остановлены.")
        page.update()

    # --- ПЕРЕПРИВЯЗКА ПРАВОЙ КОЛОНКИ (убедись, что используешь эти переменные) ---
    # (Если ты уже вставил right_column из части 2, просто убедись, что
    # phone_wrapper и terminal_box подставлены в соответствующие места в right_column)

    print(">>> [VISUAL_BUILDER] Инициализация завершена успешно.")
