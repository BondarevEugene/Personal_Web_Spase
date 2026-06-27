import flet as ft


def main(page: ft.Page):
    # Настройки портала
    page.title = "OmniFactory // EVO CORE"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.expand = True

    # Твой интерфейс: кнопки, панели, терминалы (переноси сюда из HTML)
    # Используй ft.Row и ft.Column вместо div-ов
    page.add(ft.Text("Система готова к деплою в Google Cloud", color="purple"))


# run_gui.py
import flet as ft
import httpx
import asyncio

API_URL = "http://127.0.0.1:8088"


async def main(page: ft.Page):
    page.title = "OmniFactory // ARCHITECT PANEL"
    page.theme_mode = ft.ThemeMode.DARK

    # Пример вызова твоего API
    async def load_modules(e):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_URL}/api/v1/registry")
            # Здесь будет код отрисовки модулей из resp.json()
            print(resp.json())

    btn_load = ft.ElevatedButton("Загрузить модули", on_click=load_modules)
    page.add(btn_load)






if __name__ == "__main__":
    # Для разработки локально
    ft.app(target=main, port=8089, view=ft.AppView.WEB_BROWSER)