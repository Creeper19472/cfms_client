# type: ignore
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection
from include.request import build_request
from include.transfer import receive_file_from_server
from datetime import datetime

# from common.navigation import MyNavBar

# Enhanced Colors & Styles
PRIMARY_COLOR = "#4f46e5"  # Deep indigo for primary actions
PLACEHOLDER_COLOR = "#9ca3af"  # Softer neutral for hint text
FIELD_BG = "#1f2937"  # Dark slate for input fields
BORDER_COLOR = "#374151"  # Neutral border with good contrast
TEXT_COLOR = "#f3f4f6"  # Near-white for clarity
ERROR_COLOR = "#f87171"  # Softer red for errors
SUCCESS_COLOR = "#34d399"  # Minty green for success
BUTTON_RADIUS = 12  # Slightly smaller for a sharper modern look
FORM_WIDTH = 380

current_directory_id = ""

class MyNavBar(ft.NavigationBar):
    def __init__(self):
        super().__init__(
            [
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER, label="Files"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ],
            selected_index=1,
            on_change=self.on_change_item,
            # visible=False
        )

    def on_change_item(self, e):
        match e.control.selected_index:
            case 0:  # Files
                files_container.visible = True
                home_container.visible = False
                load_directory(self.page, folder_id=current_directory_id)

            case 1:
                files_container.visible = False
                home_container.visible = True
                self.page.update()
            case 2:
                files_container.visible = False
                home_container.visible = False
                self.page.update()
            # case 3:
            #     self.page.go("/rounds")
            # case 4:
            #     self.page.go("/logos")
            # case 5:
            #     self.page.go("/slides")


def send_error(page: ft.Page, message: str):
    error_snack_bar = ft.SnackBar(
        content=ft.Text(message),
        show_close_icon=True,
        duration=4.0,
        behavior=ft.SnackBarBehavior.FLOATING,
        bgcolor=ERROR_COLOR,
    )
    page.open(error_snack_bar)


def load_directory(page: ft.Page, folder_id=None):
    global current_directory_id
    current_directory_id = folder_id

    loading_animation.visible = True
    file_listview.visible = False
    page.update()

    response = build_request(
        page,
        action="list_directory",
        data={"folder_id": folder_id},
        username=page.session.get("username"),
        token=page.session.get("token"),
    )
    loading_animation.visible = False
    page.update()
    if (code := response["code"]) != 200:
        send_error(page, f"加载失败: ({code}) {response['message']}")
    else:
        update_file_controls(response["data"]["folders"], response["data"]["documents"])
        file_listview.visible = True
        file_listview.update()


def open_document(page: ft.Page, document_id: str):
    response = build_request(
        page,
        action="get_document",
        data={"document_id": document_id},
        username=page.session.get("username"),
        token=page.session.get("token"),
    )

    task_data = response["data"]["task_data"]
    task_id = task_data["task_id"]
    task_start_time = task_data["start_time"]
    task_end_time = task_data["end_time"]
    receive_file_from_server(page, task_id)



def update_file_controls(folders: list[dict], documents: list[dict]):
    file_listview.controls = [
        ft.ListTile(
            leading=ft.Icon(ft.Icons.FOLDER),
            title=ft.Text(folder["name"]),
            subtitle=ft.Text(f"Last modified: {folder['last_modified']}"),
            on_click=lambda e: load_directory(e.page, folder_id=folder["id"]),
        )
        for folder in folders
    ]
    file_listview.controls.extend(
        [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FILE_COPY),
                title=ft.Text(document["title"]),
                subtitle=ft.Text(
                    f"Last modified: {datetime.fromtimestamp(document['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                on_click=lambda e: open_document(e.page, document["id"]),
            )
            for document in documents
        ]
    )
    file_listview.update()


loading_animation = ft.Row(
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

file_listview = ft.ListView(
    expand=True,
    visible=False,  # Initially hidden
)

files_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("文件管理", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    ft.IconButton(
                        ft.Icons.ADD, on_click=lambda e: print("Upload File")
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE, on_click=lambda e: print("Delete File")
                    ),
                    ft.IconButton(
                        ft.Icons.FOLDER_OPEN, on_click=lambda e: print("Open Folder")
                    ),
                    ft.IconButton(
                        ft.Icons.REFRESH, on_click=lambda e: load_directory(e.page, current_directory_id)
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            ft.Divider(),
            ft.Text("当前文件列表:", size=18),
            loading_animation,
            # File list, initially hidden until loading is complete
            file_listview,
        ]
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.top_center,
    visible=False,
)

home_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("落霞与孤鹜齐飞，秋水共长天一色。", size=22),
        ]
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.center,
    visible=True,
)


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

    navigation_bar = MyNavBar()
    controls = [home_container, files_container]
