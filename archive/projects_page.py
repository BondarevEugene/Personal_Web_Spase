import flet as ft
import json

def build_projects_view(state, select_project_callback, add_log_callback):
    """Строит сетку общих проектов экосистемы из внешнего JSON"""
    projects_grid = ft.Column(spacing=20, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    config_file = "projects_config.json"
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            my_projects = json.load(f)
    except FileNotFoundError:
        my_projects = []
        add_log_callback("error: projects_config.json not found")
    except Exception as ex:
        add_log_callback(f"error loading projects: {str(ex)}")
        my_projects = []

    for proj in my_projects:
        is_selected = state["selected_project_id"] == proj["id"]

        def make_select_handler(p_id, p_color):
            return lambda e: select_project_callback(p_id, p_color)

        projects_grid.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Container(
                            # ИСПРАВЛЕНО: Безопасный метод .get() предотвращает KeyError
                            content=ft.Text(proj.get("image_placeholder", "⚡ OMNI_NODE"), size=10, weight="bold", color="white",
                                            text_align=ft.TextAlign.CENTER),
                            alignment=ft.alignment.center
                        ),
                        width=140, height=120, bgcolor="#09090b", border_radius=6, border=ft.Border.all(1, "#27272a")
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(proj["icon"], color=proj["color"], size=20),
                                ft.Text(proj["title"], size=18, weight="bold", color="white"),
                            ], spacing=8),
                            ft.Container(
                                content=ft.Text(proj["status"], size=10, color="black", weight="bold"),
                                bgcolor=proj["color"], padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=460),
                        ft.Text(proj["subtitle"], size=12, color=proj["color"], italic=True),
                        ft.Text(proj["desc"], size=12, color="#94a3b8", max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row([
                            ft.TextButton("Развернуть HTML Презентацию",
                                          icon="html",
                                          icon_color=proj["color"] if is_selected else "#71717a",
                                          on_click=make_select_handler(proj["id"], proj["color"])),
                            ft.TextButton("Репозиторий", icon="code", icon_color="#71717a", url=proj["repo"])
                        ], spacing=10)
                    ], spacing=6, expand=True)
                ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15, bgcolor="#18181b", border_radius=8,
                border=ft.Border.all(1, proj["color"] if is_selected else "#27272a"), width=640
            )
        )
    return projects_grid