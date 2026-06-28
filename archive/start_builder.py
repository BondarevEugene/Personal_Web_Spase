# start_builder.py
import flet as ft
from visual_builder import build_papa_bots_view

if __name__ == "__main__":
    print(">>> Запуск независимого билдера на 127.0.0.1:8089...")
    ft.app(target=build_papa_bots_view, port=8089, host="127.0.0.1", view=None)