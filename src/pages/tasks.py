import flet as ft
from flet_model import Model, route
from include.request import build_request


@route("tasks")
class TasksModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = True
    fullscreen_dialog = True

    controls = []

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Tasks"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
        )

    def go_back(self, e):
        self.page.views.pop()
        if not self.page.views:
            self.page.go("/home")
        else:
            assert self.page.views[-1].route
            self.page.go(self.page.views[-1].route)
