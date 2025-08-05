# type: ignore
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection
from common.notifications import send_error
from include.request import build_request
from include.transfer import receive_file_from_server, upload_file_to_server
from datetime import datetime
import threading, os
from include.upload import upload_directory, filepicker_ref
from include.quotes import get_quote
from include.function.lockdown import go_lockdown

"""
Why not add a logout button to the user interface...... Well, we tried.

But the problem is that we haven't found a suitable way to gracefully reset 
all the UI modifications caused by the previous user - especially on the 
navigation_bar modifications - and some of the UI's buttons are left there 
incorrectly, causing illusions, and creating confusion.
"""

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
        self.last_selected_index = 2  # 默认值设置成初次进入时默认选中的页面在效果上较好

        nav_destinations = [
            ft.NavigationBarDestination(icon=ft.Icons.FOLDER, label="Files"),
            ft.NavigationBarDestination(icon=ft.Icons.ARROW_CIRCLE_DOWN, label="Tasks"),
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.MORE_HORIZ, label="More"),
        ]

        super().__init__(
            nav_destinations,
            selected_index=2,
            on_change=self.on_change_item,
            # visible=False
        )

    def on_change_item(self, e: ft.ControlEvent):
        control: MyNavBar = e.control
        match control.selected_index:
            case 0:  # Files
                files_container.visible = True
                home_container.visible = False
                settings_container.visible = False
                load_directory(self.page, folder_id=current_directory_id)

            case 1:
                control.selected_index = control.last_selected_index
                self.page.go("/home/tasks#object_type=document")
            case 2:
                files_container.visible = False
                home_container.visible = True
                settings_container.visible = False
                self.page.update()
            case 3:
                files_container.visible = False
                home_container.visible = False
                settings_container.visible = True
                settings_avatar.content = ft.Text(
                    self.page.session.get("username")[0].upper()
                )
                _nickname = self.page.session.get("nickname")
                settings_username_display.value = (
                    _nickname if _nickname else self.page.session.get("username")
                )
                self.page.update()
            case 4:
                control.selected_index = control.last_selected_index
                _refresh_user_list_function: function = self.page.session.get(
                    "refresh_user_list"
                )
                _refresh_user_list_function(e.page, _update_page=False)
                self.page.go("/home/manage")
            # case 4:
            #     self.page.go("/logos")
            # case 5:
            #     self.page.go("/slides")
        control.last_selected_index = control.selected_index


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
            width=400,
            alignment=ft.alignment.center,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        actions=[
            submit_button,
            this_loading_animation,
            cancel_button,
        ],
        # scrollable=True,
        # alignment=ft.MainAxisAlignment.CENTER,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

    def create_directory(page: ft.Page, name: str, parent_id=None):
        folder_name_field.disabled = True
        cancel_button.disabled = True
        this_loading_animation.visible = True
        dialog.modal = True
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

        page.close(dialog)
        load_directory(page, folder_id=current_directory_id)


def load_directory(page: ft.Page, folder_id=None):
    global current_directory_id
    _fallback_directory_id = current_directory_id
    current_directory_id = folder_id

    page.session.set("current_directory_id", current_directory_id)

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
        update_file_controls([], [], _fallback_directory_id)
        file_listview.visible = True
        file_listview.update()
        send_error(page, f"加载失败: ({code}) {response['message']}")
    else:
        update_file_controls(
            response["data"]["folders"],
            response["data"]["documents"],
            response["data"]["parent_id"],
        )
        file_listview.visible = True
        file_listview.update()


def open_document(page: ft.Page, document_id: str, filename: str):
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

    # Create a new thread to handle the file receiving process
    thread = threading.Thread(
        target=receive_file_from_server, args=(page, task_id, filename)
    )
    thread.start()
    # receive_file_from_server(page, task_id)


def upload_file(page: ft.Page):

    # fallback
    page.session.set("current_directory_id", current_directory_id)

    def pick_files_result(e: ft.FilePickerResultEvent | None):
        if not e.files:
            return

        progress_bar = ft.ProgressBar()
        progress_info = ft.Text(
            f"正在准备上传", text_align="center", color=ft.Colors.WHITE
        )
        progress_column = ft.Column(
            controls=[progress_bar, progress_info],
            # alignment=(
            #     ft.MainAxisAlignment.START
            #     if os.name == "nt"
            #     else ft.MainAxisAlignment.END
            # ),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 预定义取消按钮
        _cancel_button = ft.TextButton()

        # 设置终止标志
        _stop_flag = False

        def _cancel_upload(e: ft.ControlEvent):
            _cancel_button.disabled = True
            page.update()

            nonlocal _stop_flag
            _stop_flag = True

        _ok_button = ft.TextButton(
            "确定",
            visible=True,
            on_click=lambda _: page.close(upload_dialog),
        )

        _cancel_button.on_click = _cancel_upload
        _cancel_button.text = "取消"

        if len(e.files) > 1:
            upload_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("批量上传"),
                content=ft.Column(
                    controls=[progress_column],
                    # spacing=15,
                    width=400,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                actions=[
                    # _ok_button,
                    _cancel_button,
                ],
            )
            page.open(upload_dialog)

        for each_file in e.files:

            if _stop_flag:
                break

            if len(e.files) > 1:
                current_number = e.files.index(each_file) + 1

                progress_bar.value = current_number / len(e.files)
                progress_info.value = f"正在上传文件 [{current_number}/{len(e.files)}]"
                page.update()

            response = build_request(
                page,
                action="create_document",
                data={
                    "title": each_file.name,
                    "folder_id": current_directory_id,
                    "access_rules": {},
                },
                username=page.session.get("username"),
                token=page.session.get("token"),
            )

            if (code := response["code"]) != 200:
                if code == 403:
                    send_error(
                        page,
                        f"上传失败: 无权上传文件",
                    )
                    return
                else:
                    send_error(
                        page,
                        f"上传失败: ({response['code']}) {response['message']}",
                    )
                    continue

            task_id = response["data"]["task_data"]["task_id"]

            def handle_file_upload(page, task_id):
                try:
                    upload_file_to_server(
                        page, response["data"]["task_data"]["task_id"], each_file.path
                    )
                except Exception as exc:
                    _new_error_text = ft.Text(
                        f'在上传 "{each_file.name}" 时遇到问题: {exc}',
                        text_align=ft.TextAlign.CENTER,
                        # color=ft.Colors.RED,
                    )
                    progress_column.controls.append(_new_error_text)
                    page.update()

            # Create a new thread to handle the file uploading process
            thread = threading.Thread(target=handle_file_upload, args=(page, task_id))
            thread.start()
            thread.join()  # Wait for the thread to finish

        if len(e.files) > 1:
            if len(progress_column.controls) <= 2:
                page.close(upload_dialog)
            else:
                upload_dialog.actions.insert(0, _ok_button)
                _cancel_button.disabled = True
                page.update()

    filepicker_ref.current.on_result = pick_files_result
    filepicker_ref.current.pick_files(allow_multiple=True)


def update_mouse_position(e: ft.HoverEvent):
    e.page.session.set("mouse_x", e.global_x)
    e.page.session.set("mouse_y", e.global_y)
    return


def on_folder_right_click_menu(e: ft.ControlEvent):
    # this_loading_animation = ft.ProgressRing(visible=False)

    def delete_directory(inner_event: ft.ControlEvent):
        menu_listview.disabled = True
        dialog.modal = True
        dialog.update()  # 时间可能会较长，因此先禁用

        response = build_request(
            inner_event.page,
            action="delete_directory",
            data={"folder_id": e.control.content.data[0]},
            username=inner_event.page.session.get("username"),
            token=inner_event.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(inner_event.page, f"删除失败: ({code}) {response['message']}")
        else:
            load_directory(inner_event.page, folder_id=current_directory_id)

        dialog.open = False
        inner_event.page.update()

    def rename_directory(inner_event):
        inner_event.page.close(dialog)

        ### 弹出重命名窗口
        this_loading_animation = ft.ProgressRing(visible=False)

        def request_rename_directory(secondary_inner_event):
            folder_name_field.disabled = True
            cancel_button.disabled = True
            this_loading_animation.visible = True
            new_dialog.modal = True
            new_dialog.actions.remove(submit_button)
            inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="rename_directory",
                data={
                    "folder_id": e.control.content.data[0],
                    "new_name": folder_name_field.value,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                send_error(
                    inner_event.page, f"重命名失败: ({code}) {response['message']}"
                )
            else:
                load_directory(inner_event.page, folder_id=current_directory_id)

            inner_event.page.close(new_dialog)

        folder_name_field = ft.TextField(
            label="目录的新名称",
            value=e.control.content.data[1],
            on_submit=request_rename_directory,
            autofocus=True,
        )
        submit_button = ft.TextButton("重命名", on_click=request_rename_directory)
        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(new_dialog)
        )

        new_dialog = ft.AlertDialog(
            title=ft.Text("重命名文件夹"),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[
                    folder_name_field,
                ],
                # spacing=15,
                width=400,
                alignment=ft.alignment.center,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            actions=[
                submit_button,
                this_loading_animation,
                cancel_button,
            ],
            # scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(new_dialog)

    def open_directory_info(inner_event: ft.ControlEvent):
        e.page.close(dialog)

        this_loading_animation = ft.ProgressRing(visible=True)

        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(info_dialog)
        )

        info_listview = ft.ListView(visible=False)

        def request_directory_info(secondary_inner_event: ft.ControlEvent):

            this_loading_animation.visible = True
            info_listview.visible = False
            secondary_inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="get_directory_info",
                data={
                    "directory_id": e.control.content.data[0],
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                e.page.close(info_dialog)
                send_error(
                    inner_event.page,
                    f"拉取目录信息失败: ({code}) {response['message']}",
                )
            else:
                info_listview.controls = [
                    ft.Text(
                        f"目录ID: {response['data']['directory_id']}", selectable=True
                    ),
                    ft.Text(f"目录名称: {response['data']['name']}", selectable=True),
                    ft.Text(
                        f"子对象数: {response['data']['count_of_child']}",
                    ),
                    ft.Text(
                        f"创建于: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}",
                    ),
                    ft.Text(
                        f"父级目录ID: {response['data']['parent_id']}", selectable=True
                    ),
                    ft.Text(
                        f"访问规则: {response['data']['access_rules'] if not response['data']['info_code'] else "Unavailable"}",
                        selectable=True,
                    ),
                ]
                this_loading_animation.visible = False
                info_listview.visible = True

            e.page.update()

        info_dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("目录详情"),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=request_directory_info,
                    ),
                ]
            ),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[this_loading_animation, info_listview],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                cancel_button,
            ],
            # scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(info_dialog)
        request_directory_info(inner_event)

    menu_listview = ft.ListView(
        controls=[
            ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DELETE),
                        title=ft.Text("删除"),
                        subtitle=ft.Text(f"删除此文件夹"),
                        on_click=delete_directory,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                        title=ft.Text("重命名"),
                        subtitle=ft.Text(f"重命名此文件夹"),
                        on_click=rename_directory,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO_OUTLINED),
                        title=ft.Text("属性"),
                        subtitle=ft.Text(f"查看该文件夹的详细信息"),
                        on_click=open_directory_info,
                    ),
                ],
                # expand=True,
                # expand_loose=True
            )
        ]
    )

    dialog = ft.AlertDialog(
        title=ft.Text("操作"),
        # title_padding=ft.padding.all(25),
        content=ft.Column(
            [menu_listview], width=400, expand=True, scroll=ft.ScrollMode.AUTO
        ),
        # scrollable=True,
        alignment=ft.alignment.center,
    )

    e.page.open(dialog)
    e.page.update()

    # print(e.control.content.data)


def on_document_right_click_menu(e: ft.ControlEvent):
    def delete_document(inner_event: ft.ControlEvent):
        response = build_request(
            inner_event.page,
            action="delete_document",
            data={"document_id": e.control.content.data[0]},
            username=inner_event.page.session.get("username"),
            token=inner_event.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(inner_event.page, f"删除失败: ({code}) {response['message']}")
        else:
            load_directory(inner_event.page, folder_id=current_directory_id)

        inner_event.page.close(dialog)

    def rename_document(inner_event: ft.ControlEvent):
        inner_event.page.close(dialog)

        ### 弹出重命名窗口
        this_loading_animation = ft.ProgressRing(visible=False)

        def request_rename_document(secondary_inner_event):
            document_title_field.disabled = True
            cancel_button.disabled = True
            this_loading_animation.visible = True
            new_dialog.modal = True
            new_dialog.actions.remove(submit_button)
            inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="rename_document",
                data={
                    "document_id": e.control.content.data[0],
                    "new_title": document_title_field.value,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                send_error(
                    inner_event.page, f"重命名失败: ({code}) {response['message']}"
                )
            else:
                load_directory(inner_event.page, folder_id=current_directory_id)

            inner_event.page.close(new_dialog)

        document_title_field = ft.TextField(
            label="文件的新名称",
            value=e.control.content.data[1],
            on_submit=request_rename_document,
            autofocus=True,
        )
        submit_button = ft.TextButton("重命名", on_click=request_rename_document)
        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(new_dialog)
        )

        new_dialog = ft.AlertDialog(
            title=ft.Text("重命名文件"),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[
                    document_title_field,
                ],
                # spacing=15,
                width=400,
                alignment=ft.alignment.center,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                submit_button,
                this_loading_animation,
                cancel_button,
            ],
            # scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(new_dialog)

    def open_document_info(inner_event: ft.ControlEvent):
        e.page.close(dialog)

        this_loading_animation = ft.ProgressRing(visible=True)

        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(info_dialog)
        )

        info_listview = ft.ListView(visible=False)

        def request_document_info(secondary_inner_event: ft.ControlEvent):

            this_loading_animation.visible = True
            info_listview.visible = False
            secondary_inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="get_document_info",
                data={
                    "document_id": e.control.content.data[0],
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                e.page.close(info_dialog)
                send_error(
                    inner_event.page,
                    f"拉取文档信息失败: ({code}) {response['message']}",
                )
            else:
                info_listview.controls = [
                    ft.Text(
                        f"文档ID: {response['data']['document_id']}", selectable=True
                    ),
                    ft.Text(f"文档标题: {response['data']['title']}", selectable=True),
                    ft.Text(f"文档大小: {response['data']['size']}"),
                    ft.Text(
                        f"创建于: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}",
                    ),
                    ft.Text(
                        f"最后更改时间: {datetime.fromtimestamp(response['data']['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}",
                    ),
                    ft.Text(
                        f"父级目录ID: {response['data']['parent_id']}", selectable=True
                    ),
                    ft.Text(
                        f"访问规则: {response['data']['access_rules'] if not response['data']['info_code'] else "Unavailable"}",
                        selectable=True,
                    ),
                ]
                this_loading_animation.visible = False
                info_listview.visible = True

            e.page.update()

        info_dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("文档详情"),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=request_document_info,
                    ),
                ]
            ),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[this_loading_animation, info_listview],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            actions=[
                cancel_button,
            ],
            # scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(info_dialog)
        request_document_info(inner_event)

    def move_document(inner_event: ft.ControlEvent):
        # 初始化要传递的数据
        # e.page.session.set("move_object_type", "document")
        # e.page.session.set("move_document_id", e.control.content.data[0])
        # e.page.session.set("current_directory_id", current_directory_id) # 用于判断是否为无意义移动
        e.page.close(dialog)
        e.page.go(
            f"/home/move_object#object_type=document&object_id={e.control.content.data[0]}&current_directory_id={current_directory_id}"
        )  # 我们是客户端，不用怀疑服务端，对吧？

    def set_document_access_rules(inner_event: ft.ControlEvent):
        e.page.close(dialog)

    menu_listview = ft.ListView(
        controls=[
            ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DELETE),
                        title=ft.Text("删除"),
                        subtitle=ft.Text(f"删除此文件"),
                        on_click=delete_document,
                    ),
                    # ft.ListTile(
                    #     leading=ft.Icon(ft.Icons.DRIVE_FILE_MOVE_OUTLINED),
                    #     title=ft.Text("移动"),
                    #     subtitle=ft.Text(f"将文件移动到其他位置"),
                    #     on_click=move_document,
                    # ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                        title=ft.Text("重命名"),
                        subtitle=ft.Text(f"重命名此文件"),
                        on_click=rename_document,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED),
                        title=ft.Text("设置权限"),
                        subtitle=ft.Text(f"对此文件的访问规则进行变更"),
                        on_click=set_document_access_rules,
                        visible="set_access_rules"
                        in e.page.session.get("user_permissions"),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO_OUTLINED),
                        title=ft.Text("属性"),
                        subtitle=ft.Text(f"查看该文件的详细信息"),
                        on_click=open_document_info,
                    ),
                ],
            )
        ]
    )

    dialog = ft.AlertDialog(
        title=ft.Text("操作"),
        content=ft.Column(
            [menu_listview], width=400, expand=True, scroll=ft.ScrollMode.AUTO
        ),
        # scrollable=True,
        alignment=ft.alignment.center,
    )

    e.page.open(dialog)
    # e.page.update()


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
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER),
                    title=ft.Text(folder["name"]),
                    subtitle=ft.Text(
                        f"Created time: {datetime.fromtimestamp(folder['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                    data=(folder["id"], folder["name"]),
                    on_click=lambda e: load_directory(e.page, e.control.data[0]),
                ),
                on_secondary_tap=on_folder_right_click_menu,
                on_long_press_start=on_folder_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for folder in folders
        ]
    )
    file_listview.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FILE_COPY),
                    title=ft.Text(document["title"]),
                    subtitle=ft.Text(
                        f"Last modified: {datetime.fromtimestamp(document['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                        + (
                            f"{document["size"] / 1024 / 1024:.3f} MB"
                            if document["size"]
                            else ""
                        )
                    ),
                    is_three_line=True,
                    data=(document["id"], document["title"]),
                    on_click=lambda e: open_document(e.page, *e.control.data),
                ),
                on_secondary_tap=on_document_right_click_menu,
                on_long_press_start=on_document_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
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
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: upload_file(e.page)),
                    # ft.IconButton(
                    #     ft.Icons.DELETE, on_click=lambda e: print("Delete File")
                    # ),
                    ft.IconButton(
                        ft.Icons.DRIVE_FOLDER_UPLOAD_OUTLINED, on_click=upload_directory
                    ),
                    ft.IconButton(
                        ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
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
        ],
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.top_center,
    visible=False,
    expand=True,
)

home_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("落霞与孤鹜齐飞，秋水共长天一色。", size=22),
        ],
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.center,
    visible=True,
)

settings_avatar = ft.CircleAvatar(
    # foreground_image_src="https://avatars.githubusercontent.com/u/_5041459?s=88&v=4",
    content=ft.Text(),
)
settings_username_display = ft.Text(color=ft.Colors.WHITE)

settings_container = ft.Container(
    content=ft.Column(
        controls=[
            # Avatar frame
            ft.Row(
                controls=[
                    settings_avatar,
                    ft.Column(
                        controls=[
                            settings_username_display,
                            ft.Text(get_quote()),
                        ],
                        spacing=0,
                    ),
                ]
            ),
            ft.Divider(),
            # Menu entries below the avatar
            ft.ListView(
                controls=[
                    # ft.ListTile(
                    #     leading=ft.Icon(ft.Icons.ACCOUNT_CIRCLE),
                    #     title=ft.Text("个人资料"),
                    #     on_click=lambda e: e.page.go("/profile"),
                    # ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.SETTINGS),
                        title=ft.Text("设置"),
                        on_click=lambda e: e.page.go("/home/settings"),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO),
                        title=ft.Text("关于"),
                        on_click=lambda e: e.page.go("/home/about"),
                    ),
                ]
            ),
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
    ),
    margin=10,
    padding=10,
    visible=False,  # Initially hidden
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

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.page.session.set("navigation_bar", self.navigation_bar)

    controls = [
        ft.SafeArea(ft.Container()),
        home_container,
        files_container,
        settings_container,
    ]

    def post_init(self) -> None:
        self.page.overlay.append(filepicker_ref.current)
        self.page.update()

        self.page.session.set("load_directory", load_directory)
        self.page.session.set("current_directory_id", current_directory_id)
        self.page.session.set("initialization_complete", True)

        if self.page.session.get("server_info")[
            "lockdown"
        ] and "bypass_lockdown" not in self.page.session.get("user_permissions"):
            go_lockdown(self.page)
