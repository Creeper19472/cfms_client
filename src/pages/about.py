import flet as ft
from flet_model import Model, route
from include.request import build_request
from common.notifications import send_error

@route("about")
class AboutModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    appbar = ft.AppBar(
        title=ft.Text("About"),
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.go("/home")
        ),
    )

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.about_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Classified File Management System Client", size=22, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"Version: {page.session.get("version")}", size=16, text_align=ft.TextAlign.CENTER),
                    ft.Text("Copyright © 2025", size=16, text_align=ft.TextAlign.CENTER),
                    ft.Text("Licensed under Apache License Version 2.0.", size=16, text_align=ft.TextAlign.CENTER),

                ],
            ),
            margin=10,
            padding=10,
            # alignment=ft.alignment.center,
            visible=True,
        )
        self.controls = [self.about_container]