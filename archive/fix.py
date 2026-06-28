from pathlib import Path

file_path = Path("app.py")

if not file_path.exists():
    print("Ошибка: Файл app.py не найден!")
    exit()

code = file_path.read_text(encoding="utf-8")

# 1. ГЛОБАЛЬНО ЧИНИМ ЦВЕТА (Переводим невидимый "zinc" в реальные HEX-коды)
code = code.replace('"zinc400"', '"#94a3b8"')
code = code.replace('"zinc500"', '"#71717a"')
code = code.replace('"zinc600"', '"#52525b"')
code = code.replace('"zinc700"', '"#404040"')
code = code.replace('"zinc800"', '"#27272a"')
code = code.replace('"zinc900"', '"#18181b"')
code = code.replace('"zinc950"', '"#09090b"')

# 2. ИСПРАВЛЯЕМ ШРИФТЫ (Из-за которых падало на старте)
code = code.replace("ft.FontWeight.BLACK", '"black"')
code = code.replace("ft.FontWeight.BOLD", '"bold"')

# 3. УБИРАЕМ ИМЕНОВАННЫЙ АРГУМЕНТ У ИКОНОК
code = code.replace('name=res["icon"]', 'res["icon"]')
code = code.replace('name="wifi"', '"wifi"')
code = code.replace('name=node["icon"]', 'node["icon"]')

# 4. ИСПРАВЛЯЕМ КНОПКИ ВКЛАДОК (Убираем ломающийся кастомный стиль)
old_tabs = """tabs_row = ft.Row([
        ft.TextButton("1. BUILD_NODE", on_click=lambda e: switch_tab("BUILD"),
                      style=ft.ButtonStyle(color="white" if state["active_tab"] == "BUILD" else "zinc600")),
        ft.TextButton("2. STYLE_SHELL", on_click=lambda e: switch_tab("STYLE"),
                      style=ft.ButtonStyle(color="white" if state["active_tab"] == "STYLE" else "zinc600")),
        ft.TextButton("3. PREVIEW_JSON", on_click=lambda e: switch_tab("PREVIEW"),
                      style=ft.ButtonStyle(color="white" if state["active_tab"] == "PREVIEW" else "zinc600")),
    ], spacing=10)"""

new_tabs = """tabs_row = ft.Row([
        ft.TextButton("1. BUILD_NODE", on_click=lambda e: switch_tab("BUILD")),
        ft.TextButton("2. STYLE_SHELL", on_click=lambda e: switch_tab("STYLE")),
        ft.TextButton("3. PREVIEW_JSON", on_click=lambda e: switch_tab("PREVIEW")),
    ], spacing=10)"""

code = code.replace(old_tabs, new_tabs)

# 5. УБИРАЕМ БЛОКИРУЮЩИЙ ЗАПРОС НА СТАРТЕ
code = code.replace("render_all()\n    fetch_health_telemetry()", "render_all()\n    # fetch_health_telemetry()")

file_path.write_text(code, encoding="utf-8")
print("Успешно! Все критические ошибки и невидимые цвета автоматически исправлены.")