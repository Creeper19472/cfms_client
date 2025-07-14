import flet as ft
from flet_model import Model, route
from include.request import build_request


@route("/move_document")
class MoveDocumentModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = True

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Move Document To..."),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
        )

        print("init")

    def go_back(self, e):
        self.page.views.pop()
        self.update()
