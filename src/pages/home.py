# type: ignore
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection
from include.request import build_request
from include.transfer import receive_file_from_server, upload_file_to_server
from datetime import datetime
import threading, json

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
    page.overlay.append(error_snack_bar)
    error_snack_bar.open = True
    page.update()


def open_create_directory_form(page: ft.Page):

    this_loading_animation = ft.ProgressRing(visible=False)

    folder_name_field = ft.TextField(
        label="目录名称",
        on_submit=lambda e: create_directory(
            e.page, e.control.value, parent_id=current_directory_id
        ),
    )
    submit_button = ft.TextButton(
        "创建",
        on_click=lambda e: create_directory(
            e.page, folder_name_field.value, parent_id=current_directory_id
        ),
    )
    cancel_button = ft.TextButton("取消", on_click=lambda e: page.close(dialog))

    dialog = ft.AlertDialog(
        title=ft.Text("创建文件夹"),
        # title_padding=ft.padding.all(25),
        content=ft.Column(
            controls=[
                folder_name_field,
            ],
            # spacing=15,
            height=50,
            width=400,
            alignment=ft.alignment.center,
        ),
        actions=[
            submit_button,
            this_loading_animation,
            cancel_button,
        ],
        # alignment=ft.MainAxisAlignment.CENTER,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

    def create_directory(page: ft.Page, name: str, parent_id=None):
        folder_name_field.disabled = True
        cancel_button.disabled = True
        this_loading_animation.visible = True
        dialog.modal = False
        # dialog.actions.remove(cancel_button)
        dialog.actions.remove(submit_button)
        page.update()

        response = build_request(
            page,
            action="create_directory",
            data={"parent_id": parent_id, "name": name},
            username=page.session.get("username"),
            token=page.session.get("token"),
        )

        if (code := response["code"]) != 200:
            send_error(page, f"Action failed: ({code}) {response['message']}")
            # folder_name_field.disabled = False
            # dialog.actions.append(submit_button)
            # cancel_button.disabled = False
            # this_loading_animation.visible = False
            page.update()
        else:
            pass
            # load_directory(page, folder_id=current_directory_id)

        page.close(dialog)
        load_directory(page, folder_id=current_directory_id)


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
        update_file_controls(
            response["data"]["folders"],
            response["data"]["documents"],
            response["data"]["parent_id"],
        )
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

    def handle_file_receive(page, task_id):
        receive_file_from_server(page, task_id)

    # Create a new thread to handle the file receiving process
    thread = threading.Thread(target=handle_file_receive, args=(page, task_id))
    thread.start()
    # receive_file_from_server(page, task_id)


def upload_file(page: ft.Page):

    page.session.set("load_directory", load_directory)
    page.session.set("current_directory_id", current_directory_id)

    def pick_files_result(e: ft.FilePickerResultEvent|None):
        if not e.files:
            return

        for each_file in e.files:
            response = build_request(
                page,
                action="create_document",
                data={
                    "title": each_file.name,
                    "folder_id": current_directory_id,
                    "access_rules": {}
                },
                username=page.session.get("username"),
                token=page.session.get("token"),
            )

            task_id = response["data"]["task_data"]["task_id"]

            def handle_file_upload(page, task_id):
                upload_file_to_server(page, response["data"]["task_data"]["task_id"], each_file.path)

            # Create a new thread to handle the file uploading process
            thread = threading.Thread(target=handle_file_upload, args=(page, task_id))
            thread.start()
        
        
        # selected_files.value = (
        #     ", ".join(map(lambda f: f.name, e.files)) if e.files else "Cancelled!"
        # )
        # selected_files.update()

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    # selected_files = ft.Text()

    page.overlay.append(pick_files_dialog)
    # page.overlay.append(selected_files)
    page.update()

    pick_files_dialog.pick_files(allow_multiple=False) # TODO


def update_file_controls(folders: list[dict], documents: list[dict], parent_id=None):
    file_listview.controls = []  # reset

    if parent_id != None:
        # print("parent_id: ", parent_id)
        file_listview.controls = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ARROW_BACK),
                title=ft.Text("<...>"),
                subtitle=ft.Text(f"Parent directory"),
                on_click=lambda e: load_directory(
                    e.page, folder_id=None if parent_id == "/" else parent_id
                ),
            )
        ]

    file_listview.controls.extend(
        [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FOLDER),
                title=ft.Text(folder["name"]),
                subtitle=ft.Text(
                    f"Last modified: {datetime.fromtimestamp(folder['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                data=folder["id"],
                on_click=lambda e: load_directory(e.page, e.control.data),
            )
            for folder in folders
        ]
    )
    file_listview.controls.extend(
        [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FILE_COPY),
                title=ft.Text(document["title"]),
                subtitle=ft.Text(
                    f"Last modified: {datetime.fromtimestamp(document['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                data=document["id"],
                on_click=lambda e: open_document(e.page, e.control.data),
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
                        ft.Icons.ADD, on_click=lambda e: upload_file(e.page)
                    ),
                    # ft.IconButton(
                    #     ft.Icons.DELETE, on_click=lambda e: print("Delete File")
                    # ),
                    # ft.IconButton(
                    #     ft.Icons.FOLDER_OPEN, on_click=lambda e: print("Open Folder")
                    # ),
                    ft.IconButton(
                        ft.Icons.CREATE_NEW_FOLDER,
                        on_click=lambda e: open_create_directory_form(e.page),
                    ),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=lambda e: load_directory(e.page, current_directory_id),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            ft.Divider(),
            # ft.Text("当前文件列表:", size=18),
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
