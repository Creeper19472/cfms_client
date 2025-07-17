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
        print("__init__ called")

    def post_init(self):
        print("post_init called")
        self.current_directory_id = self.route_data.get("current_directory_id", None)

        if self.current_directory_id == "None":
            self.current_directory_id = None

        self.load_directory(self.current_directory_id)

    def go_back(self, e: Optional[ft.ControlEvent] = None): # issue
        self.page.views.pop()
        if len(self.page.views) > 1:
            assert self.page.views[-1].route
            self.page.go(self.page.views[-1].route)
        else:
            self.page.go("/home")

    def update_file_controls(
        self, folders: list[dict], documents: list[dict], parent_id=None
    ):
        self.file_listview.controls = []  # reset

        if parent_id != None:
            # print("parent_id: ", parent_id)
            self.file_listview.controls = [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ARROW_BACK),
                    title=ft.Text("<...>"),
                    subtitle=ft.Text(f"Parent directory"),
                    on_click=lambda e: self.load_directory(
                        folder_id=None if parent_id == "/" else parent_id
                    ),
                )
            ]

        self.file_listview.controls.extend(
            [
                # ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER),
                    title=ft.Text(folder["name"]),
                    subtitle=ft.Text(
                        f"Created time: {datetime.fromtimestamp(folder['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                    data=(folder["id"], folder["name"]),
                    on_click=lambda e: self.load_directory(e.control.data[0]),
                    # trailing=ft.Checkbox(on_change=self.action_move, data=folder["id"]),
                )  # ,
                #     on_secondary_tap=self.page.update(), # on_folder_right_click_menu,
                #     on_long_press_start=self.page.update(), # on_folder_right_click_menu,
                # )
                for folder in folders
            ]
        )
        self.file_listview.update()

    def load_directory(self, folder_id: Optional[str] = None):
        _fallback_directory_id = self.current_directory_id
        self.current_directory_id = folder_id

        self.loading_animation.visible = True
        self.file_listview.visible = False
        self.page.update()

        response = build_request(
            self.page,
            action="list_directory",
            data={"folder_id": folder_id},
            username=self.page.session.get("username"),
            token=self.page.session.get("token"),
        )
        self.loading_animation.visible = False
        self.page.update()
        if (code := response["code"]) != 200:
            self.update_file_controls([], [], _fallback_directory_id)
            self.file_listview.visible = True
            self.file_listview.update()
            send_error(self.page, f"加载失败: ({code}) {response['message']}")
        else:
            self.update_file_controls(
                response["data"]["folders"],
                response["data"]["documents"],
                response["data"]["parent_id"],
            )
            self.file_listview.visible = True
            self.file_listview.update()

    def action_move(self, event: ft.ControlEvent):
        if self.route_data.get("object_type") == "document":
            response = build_request(
                self.page,
                "move_document",
                data={
                    "document_id": self.route_data.get("object_id"),
                    "target_folder_id": self.current_directory_id # event.control.data,
                },
                username=self.page.session.get("username"),
                token=self.page.session.get("token"),
            )
        else:
            raise

        if response["code"] != 200:
            send_error(
                self.page,
                f"移动失败: ({response['code']}) {response['message']}",
            )
        
        self.go_back()
