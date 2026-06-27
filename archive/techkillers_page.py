import flet as ft
import json


def build_techkillers_view(add_log_callback, render_all_callback):
    """Строит панель управления и мониторинга для Техкиллерс"""
    techkillers_grid = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    try:
        with open("techkillers_config.json", "r", encoding="utf-8") as f:
            tk_modules = json.load(f)
    except FileNotFoundError:
        tk_modules = []
        add_log_callback("error: techkillers_config.json not found")

    techkillers_grid.controls.append(
        ft.Row([
            ft.Text("NUMEROLOGY_PROCESSOR_CONTROL_PANEL //", size=12, weight="bold", color="#f97316"),
            ft.Text(f"ACTIVE_NODES: {len(tk_modules)}", size=11, color="#71717a")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=620)
    )

    for mod in tk_modules:
        def make_test_handler(m_name):
            return lambda e: (add_log_callback(f"ping sent to {m_name}... status: operational"), render_all_callback())

        techkillers_grid.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(mod["icon"], color="#f97316", size=24),
                            ft.Container(
                                content=ft.Text(mod["type"], size=8, color="black", weight="bold"),
                                bgcolor="#f97316", padding=3, border_radius=3
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5),
                        width=100, height=100, bgcolor="#09090b", border_radius=6, border=ft.Border.all(1, "#27272a")
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(mod["name"], size=15, weight="bold", color="white"),
                            ft.Row([
                                ft.Text(f"Latency: {mod['speed']}", size=11, color="#71717a"),
                                ft.Container(width=8, height=8, border_radius=4,
                                             bgcolor="green" if mod["status"] == "OPERATIONAL" else "yellow")
                            ], spacing=10)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=490),
                        ft.Text(mod["desc"], size=11, color="#94a3b8", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Divider(color="#27272a", height=5),
                        ft.Row([
                            ft.Text(f"Telemetry: {mod['metrics']}", size=10, font_family="JetBrains Mono",
                                    color="#00FF41"),
                            ft.TextButton("RUN_DIAGNOSTIC", icon="play_arrow", icon_color="#71717a",
                                          on_click=make_test_handler(mod["name"]))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=490)
                    ], spacing=4, expand=True)
                ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=12, bgcolor="#141416", border_radius=8, border=ft.Border.all(1, "#27272a"), width=620
            )
        )
    return techkillers_grid
