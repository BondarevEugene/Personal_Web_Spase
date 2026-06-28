# start_ui.py
import flet as ft
from visual_builder import build_papa_bots_view

if __name__ == "__main__":
    # Разрешаем CORS
    import os

    os.environ["FLET_WS_ALLOWED_ORIGINS"] = "*"
    os.environ["FLET_WEB_ALLOW_ORIGINS"] = "*"

    # Запуск конструктора
    ft.app(
        target=build_papa_bots_view,
        port=8089,
        view=ft.AppView.WEB_BROWSER
    )