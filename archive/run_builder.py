import flet as ft
import sys
# Убедись, что visual_builder.py лежит рядом
from visual_builder import build_papa_bots_view

def main(page: ft.Page):
    # Если эта функция вызовется, значит Flet работает
    page.add(ft.Text("СТАРТ УСПЕШЕН", size=40))

if __name__ == "__main__":
    print(">>> Запуск билдера в тестовом режиме...")
    try:
        # Пытаемся запустить твою функцию
        ft.run(build_papa_bots_view, port=8089, host="127.0.0.1", view=ft.AppView.WEB_BROWSER)
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        input("Нажми Enter чтобы закрыть...")