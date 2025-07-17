from typing import Optional
import flet as ft
from flet_model import Model, route
from include.request import build_request
from common.notifications import send_error
from datetime import datetime


@route("move_object")
class MoveObjectModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = True

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.current_directory_id: str | None = ""

        self.appbar = ft.AppBar(
            title=ft.Row(
                controls=[
                    ft.Text("Move Document To..."),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=lambda e: self.load_directory(
                            self.current_directory_id
                        ),
                    ),
                ]
            ),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            actions=[
                ft.TextButton(
                    icon=ft.Icons.CHECK,
                    text="Confirm",
                    on_click=self.action_move,
                    data=self.current_directory_id,
                )
            ],
        )

        self.loading_animation = ft.Row(
            controls=[
                ft.ProgressRing(
                    visible=True,
                    width=40,
                    height=40,
                    stroke_width=4,
                    value=None,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.file_listview = ft.ListView(
            expand=True,
            visible=False,  # Initially hidden
        )

        self.files_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.loading_animation,
                    # File list, initially hidden until loading is complete
                    self.file_listview,
                ],
            ),
            margin=10,
            padding=10,
            alignment=ft.alignment.top_center,
            visible=True,
            expand=True,
        )

        self.controls = [self.files_container]

    def init(self):
        print("init1")
        self.current_directory_id = self.route_data.get("current_directory_id", None)

        if self.current_directory_id == "None":
            self.current_directory_id = None

        self.load_directory(self.current_directory_id)

    def go_back(self, e: Optional[ft.ControlEvent] = None):
        self.page.views.pop()
        if self.page.views:
            assert self.page.views[-1].route
            self.page.go(self.page.views[-1].route)
        else:
            self.page.go("/home")

    def update_file_controls(
        self, folders: list[dict], documents: list[dict], parent_id=None
    ):
        pass

    def load_directory(self, folder_id: Optional[str] = None):
        pass

    def action_move(self, event: ft.ControlEvent):
        self.go_back()


@route("connect")
class ConnectToServerModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    appbar = ft.AppBar(title=ft.Text("Connect to Server"), center_title=True)

    def connect_button_clicked(self, e):
        self.page.go("/home")

    def __init__(self, page: ft.Page):
        super().__init__(page)

        # Refs
        self.server_address_ref = ft.Ref[ft.TextField]()
        self.form_container_ref = ft.Ref[ft.Container]()

        self.controls = [ft.Button("Connect", on_click=self.connect_button_clicked)]



@route("home")
class HomeModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    # # UI Components
    # appbar = ft.AppBar(
    #     title=ft.Text("Home"),
    #     center_title=True,
    #     # bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
    # )

    # navigation_bar = MyNavBar()

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.page.session.set("navigation_bar", self.navigation_bar)

    # def init(self):
    #     self.page.session.set("home", self)

    controls = [ft.Button("Hello", on_click=lambda e: e.page.go("/home/move_object"))]




def main(page: ft.Page):
    page.go("/connect")


if __name__ == "__main__":
    ft.app(target=main)
