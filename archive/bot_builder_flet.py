# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /bot_builder_flet.py
# VERSION: 4.3.0 (COCKPIT NO-CODE STABLE PRODUCTION)
# LAST MODIFIED: 2026-05-20
# DESCRIPTION: Визуальный No-Code конструктор "Папа Ботов" (Flet Engine).
# PURPOSE:
#   1. Полноразмерный трехсекционный интерфейс управления ИИ-агентами OmniFactory.
#   2. Масштаб Mind-Map сужен на 40% (через веса), телефон гарантированно влезает.
#   3. Исправлены все ломающие ошибки Flet 0.24+ (Alignment, BorderRadius, Checkbox).
# AUTHOR: Eugene Bondarev & Gemini AI Collaborator
# STATUS: Active / Production Core Engine / UTF-8 Enforced / Calibrated Layout
# ==============================================================================

import flet as ft
from services.bot_factory import MODULES_REGISTRY

def build_papa_bots_view(page: ft.Page):
    page.title = "OmniFactory EVO // Папа Ботов"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#09090e"
    page.padding = 12

    # Внутренний No-Code стейт
    selected_category = "all"
    search_query = ""
    selected_module_ids = set(["welcome"])
    active_step_idx = 0

    # Шаги диалога (Карта коммуникации ИИ)
    bot_dialog_tree = [
        {"id": "step_1", "title": "Старт Системы", "text": "🤖 Бот успешно сгенерирован на OmniFactory EVO!\n\nВыберите кубики автоматизации слева и настройте ветки логики:",
         "buttons": ["🎵 Скачать Медиа", "🧠 ИИ Консультант", "📋 Помощь"]},
        {"id": "step_2", "title": "ИИ Консультант", "type": "AI_AGENT",
         "text": "🧠 Запущен изолированный ИИ-агент OmniFactory.\n\nЗадайте ваш вопрос нейросети:",
         "buttons": ["↩ Назад", "💳 Оплата"]}
    ]

    # --- ЭЛЕМЕНТЫ СЕТКИ ИНТЕРФЕЙСА ---
    modules_list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    phone_screen_content = ft.Column(spacing=8, expand=True)
    tree_canvas_container = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    category_tabs_container = ft.Row(spacing=5, scroll=ft.ScrollMode.ADAPTIVE)

    # Элементы правого пульта (Защита от NameError)
    status_label = ft.Text("STATUS: IDLE", size=11, color="#00ffff", weight=ft.FontWeight.BOLD)
    docker_id_label = ft.Text("DOCKER: NONE", size=10, color="#71717a", weight=ft.FontWeight.BOLD)

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

    # --- ЛОГИКА ОБНОВЛЕНИЯ И ОТРИСОВКИ ---
    def render_tabs():
        category_tabs_container.controls.clear()
        labels = ["ВСЕ", "БАЗА", "ИИ", "ПРОДАЖИ", "АДМИН"]
        cats = ["all", "core", "ai", "shop", "admin"]
        for i, label in enumerate(labels):
            is_sel = (cats[i] == selected_category)
            category_tabs_container.controls.append(
                ft.Container(
                    content=ft.Text(label, size=9.5, weight=ft.FontWeight.BOLD, color="white" if is_sel else "#71717a"),
                    padding=6, bgcolor="#bc13fe" if is_sel else "transparent", border_radius=ft.border_radius.all(4),
                    on_click=lambda e, cat=cats[i]: change_category(cat)
                )
            )
        page.update()

    def change_category(cat):
        nonlocal selected_category
        selected_category = cat
        render_tabs()
        render_modules_matrix()

    def toggle_module_selection(mid, val):
        if val:
            selected_module_ids.add(mid)
        else:
            if mid != "welcome":
                selected_module_ids.discard(mid)
        page.update()

    def select_step(idx):
        nonlocal active_step_idx
        active_step_idx = idx
        node_text_input.value = bot_dialog_tree[active_step_idx]["text"]
        render_visual_tree()
        render_phone_simulator()

    def on_search_change(e):
        nonlocal search_query
        search_query = e.control.value.lower()
        render_modules_matrix()

    def update_node_text(new_val):
        bot_dialog_tree[active_step_idx]["text"] = new_val
        render_phone_simulator()
        render_visual_tree()

    node_text_input.on_change = lambda e: update_node_text(e.control.value)

    def render_modules_matrix():
        modules_list_container.controls.clear()
        for mid, info in MODULES_REGISTRY.items():
            if selected_category != "all" and info.get("cat", "") != selected_category:
                continue
            if search_query and (search_query not in info.get("label", "").lower() and search_query not in info.get("desc", "").lower()):
                continue

            is_checked = mid in selected_module_ids
            cat_colors = {"core": "#00ffff", "ai": "#bc13fe", "shop": "#ffaa00", "admin": "#ff0055"}
            neon_color = cat_colors.get(info.get("cat", "core"), "#00ffff")

            card = ft.Container(
                content=ft.Row([
                    ft.Icon(info.get("icon", "settings").lower(), color=neon_color, size=18),
                    ft.Column([
                        ft.Row([
                            ft.Text(info.get("label", "Unknown"), size=11, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Container(
                                content=ft.Text(info.get("cat", "core").upper(), size=7, weight=ft.FontWeight.BOLD, color=neon_color),
                                bgcolor="rgba(255,255,255,0.03)", padding=3, border_radius=ft.border_radius.all(2)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=160),
                        ft.Text(info.get("desc", ""), size=9.5, color="#94a3b8", width=170, max_lines=2),
                    ], spacing=1, expand=True),
                    ft.Checkbox(
                        value=is_checked, active_color="#bc13fe",
                        on_change=lambda e, m_id=mid: toggle_module_selection(m_id, e.control.value)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=8, bgcolor="#101014" if is_checked else "#0b0b0e", border_radius=ft.border_radius.all(4),
                border=ft.border.all(1, "rgba(188, 19, 254, 0.2)" if is_checked else "rgba(255,255,255,0.05)")
            )
            modules_list_container.controls.append(card)
        page.update()

    def render_phone_simulator():
        phone_screen_content.controls.clear()
        current_step = bot_dialog_tree[active_step_idx]

        phone_screen_content.max_width = 190
        phone_screen_content.controls.append(
            ft.Container(
                content=ft.Text(current_step["text"], size=10, color="white", font_family="JetBrains Mono"),
                bgcolor="#1e1e2e", padding=8,
                border_radius=ft.border_radius.only(top_left=12, top_right=12, bottom_right=12)
            )
        )

        buttons_grid = ft.Column(spacing=4)
        for btn_text in current_step["buttons"]:
            buttons_grid.controls.append(
                ft.Container(
                    content=ft.Text(btn_text, size=9.5, weight=ft.FontWeight.BOLD, color="#00ffff", text_align=ft.TextAlign.CENTER),
                    bgcolor="rgba(0, 255, 255, 0.04)", border=ft.border.all(1, "rgba(0, 255, 255, 0.25)"),
                    padding=5, border_radius=ft.border_radius.all(4), alignment=ft.Alignment(0, 0)
                )
            )
        phone_screen_content.controls.append(buttons_grid)
        page.update()

    def render_visual_tree():
        tree_canvas_container.controls.clear()
        for idx, step in enumerate(bot_dialog_tree):
            is_active = (idx == active_step_idx)
            node_colors = {"CORE": "#00ffff", "AI_AGENT": "#bc13fe", "PAYMENT": "#ffaa00"}
            current_neon = node_colors.get(step.get("type", "CORE"), "#bc13fe")

            node_box = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"БЛОК // {step['title'].upper()}", size=10, weight=ft.FontWeight.BOLD, color="#bc13fe" if is_active else "#71717a"),
                        ft.Container(ft.Text(step.get("type", "CORE"), size=7, color="black", weight=ft.FontWeight.BOLD), bgcolor=current_neon, padding=2, border_radius=ft.border_radius.all(2))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(step["text"], size=9.5, color="#cbd5e1", max_lines=1),
                    ft.Row([
                        ft.Container(ft.Text(f"🔗 {btn}", size=8.5, color="white"), bgcolor="#1a1a24", padding=3, border_radius=ft.border_radius.all(2)) for btn in step.get("buttons", [])
                    ], wrap=True, spacing=3)
                ], spacing=4),
                padding=10, bgcolor="#0e0e14" if is_active else "#0b0b0d",
                border=ft.border.all(1, "#bc13fe" if is_active else "rgba(255,255,255,0.03)"),
                border_radius=ft.border_radius.all(5), on_click=lambda e, i=idx: select_step(i)
            )
            tree_canvas_container.controls.append(node_box)

            if idx < len(bot_dialog_tree) - 1:
                next_title = bot_dialog_tree[idx + 1]["title"].upper()
                tree_canvas_container.controls.append(
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Row([
                            ft.Icon("arrow_downward", color="rgba(188, 19, 254, 0.4)", size=16),
                            ft.Text(f"МАРШРУТ ПЕРЕХОДА ──► К БЛОКУ: {next_title}", size=8, color="#4b5563", font_family="Orbitron")
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
                    )
                )
        page.update()

    def add_new_branch_step(e):
        new_idx = len(bot_dialog_tree) + 1
        bot_dialog_tree.append({
            "id": f"step_{new_idx}", "title": f"Шаг Цепочки {new_idx}", "type": "AI_AGENT",
            "text": "Архитектор, настройте промпт ИИ или сценарий ответа:",
            "buttons": ["↩ В главное меню"]
        })
        select_step(len(bot_dialog_tree) - 1)

    search_field = ft.TextField(
        label="Фильтр кубиков автоматизации...",
        border_color="rgba(188, 19, 254, 0.4)", focused_border_color="#bc13fe",
        label_style=ft.TextStyle(color="#71717a", size=10), text_style=ft.TextStyle(color="white", size=11),
        height=36, on_change=on_search_change
    )
# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /bot_builder_flet.py (ФИНАЛЬНАЯ ОПТИМИЗИРОВАННАЯ СЕТКА)
# LAST MODIFIED: 2026-05-20
# ==============================================================================
    # --- СБОРКА ТРЕХ СЕКЦИЙ С СУЖЕНИЕМ ХОЛСТА MIND-MAP НА 40% ---
    left_column = ft.Container(
        content=ft.Column([
            ft.Text("CORE MODULES", size=11, font_family="Orbitron", weight=ft.FontWeight.BOLD, color="#00ffff"),
            search_field, category_tabs_container, modules_list_container
        ], spacing=10),
        padding=10, bgcolor="#0b0b10", border_radius=ft.border_radius.all(6), width=250
    )

    # Центральный холст Mind-Map сужен до expand=2 (высвобождает место и сжимает схему на 40%)
    center_column = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("// MIND_MAP_DECISION_FLOW", size=11, font_family="Orbitron", weight=ft.FontWeight.BOLD, color="#bc13fe"),
                ft.ElevatedButton("+ ДОБАВИТЬ БЛОК", bgcolor="#bc13fe", color="white", on_click=add_new_branch_step,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color="rgba(255,255,255,0.05)", height=1),
            tree_canvas_container
        ], spacing=10),
        padding=10, bgcolor="#0b0b10", border_radius=ft.border_radius.all(6),
        expand=2  # МАСШТАБ СУЖЕН НА 40%
    )

    # ФИКС: Валидный объект Alignment(0,0) вместо упавшего ft.alignment.center
    phone_wrapper = ft.Container(
        alignment=ft.Alignment(0, 0),
        height=230,
        content=ft.Container(
            width=210, height=210, bgcolor="#0f0f14",
            border=ft.border.all(4, "#27272a"), border_radius=ft.border_radius.all(20), padding=10, content=phone_screen_content
        )
    )

    right_column = ft.Container(
        content=ft.Column([
            ft.Text("// TELEGRAM_SIMULATOR", size=11, font_family="Orbitron", weight=ft.FontWeight.BOLD, color="#71717a"),
            token_input, node_text_input,
            phone_wrapper,
            ft.Row([
                ft.ElevatedButton("LAUNCH", bgcolor="#00ff41", color="black", icon="play_arrow", expand=True,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))),
                ft.ElevatedButton("KILL", bgcolor="#ff0055", color="white",
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)))
            ], spacing=8)
        ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=10, bgcolor="#0b0b10", border_radius=ft.border_radius.all(6),
        width=310  # Жестко фиксируем ширину правого пульта, чтобы симулятор вошел на экран
    )

    page.add(ft.Row(controls=[left_column, center_column, right_column], spacing=10, expand=True))

    node_text_input.value = bot_dialog_tree[active_step_idx]["text"]
    render_tabs()
    render_modules_matrix()
    render_phone_simulator()
    render_visual_tree()
    page.update()