import flet as ft
from flet_model import Model, route
from include.request import build_request
from common.notifications import send_error
from datetime import datetime


class ManagementNavBar(ft.NavigationBar):
    def __init__(self):
        nav_destinations = [
            ft.NavigationBarDestination(
                icon=ft.Icons.SUPERVISOR_ACCOUNT_OUTLINED, label="Accounts"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
                label="User Groups & Permissions",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_APPLICATIONS, label="Settings"
            ),
        ]

        super().__init__(
            nav_destinations,
            selected_index=0,
            on_change=self.on_change_item,
            # visible=False
        )

    def on_change_item(self, e: ft.ControlEvent):
        control: ManagementNavBar = e.control
        match control.selected_index:
            case 0:  # Manage Accounts
                refresh_user_list(e.page)
                manage_accounts_container.visible = True
                e.page.update()
            #     home_container.visible = False
            #     load_directory(self.page, folder_id=current_directory_id)

            # case 1:
            #     manage_accounts_container.visible = False
            #     home_container.visible = True
            #     self.page.update()
            # case 2:
            #     manage_accounts_container.visible = False
            #     home_container.visible = False
            #     self.page.update()


def on_user_right_click_menu(e: ft.ControlEvent):
    def delete_user(inner_event: ft.ControlEvent):
        return
        response = build_request(
            inner_event.page,
            action="delete_document",
            data={"document_id": e.control.content.data},
            username=inner_event.page.session.get("username"),
            token=inner_event.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(inner_event.page, f"删除失败: ({code}) {response['message']}")
        else:
            load_directory(inner_event.page, folder_id=current_directory_id)

        inner_event.page.close(dialog)

    def rename_user(inner_event: ft.ControlEvent): # nickname
        return
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
                    "document_id": e.control.content.data,
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
            label="文件的新名称", on_submit=request_rename_document
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
            ),
            actions=[
                submit_button,
                this_loading_animation,
                cancel_button,
            ],
            scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(new_dialog)

    def view_user_info(e):
        dialog.open = False
        e.page.update()

    menu_listview = ft.ListView(
        controls=[
            ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DELETE),
                        title=ft.Text("删除"),
                        subtitle=ft.Text(f"删除此用户"),
                        on_click=delete_user,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                        title=ft.Text("更改昵称"),
                        subtitle=ft.Text(f"为用户更改昵称"),
                        on_click=rename_user,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO_OUTLINED),
                        title=ft.Text("属性"),
                        subtitle=ft.Text(f"查看该用户的详细信息"),
                        on_click=view_user_info,
                    ),
                ],
            )
        ]
    )

    dialog = ft.AlertDialog(
        title=ft.Text("操作"),
        content=ft.Column([menu_listview], width=400),
        scrollable=True,
        alignment=ft.alignment.center,
    )

    e.page.open(dialog)
    e.page.update()




def update_user_controls(users: list[dict], _update_page=True):
    user_listview.controls = []  # reset
    user_listview.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ACCOUNT_CIRCLE),
                    title=ft.Text(user["nickname"]),
                    subtitle=ft.Text(
                        f"Username: {user["username"]}\n"+
                        f"Last login: {datetime.fromtimestamp(user['last_login']).strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else "Unknown"}"
                    ),
                    is_three_line=True,
                    data=user["username"],
                    on_click=None,
                ),
                on_secondary_tap=on_user_right_click_menu,
                on_long_press_start=on_user_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for user in users
        ]
    )
    if _update_page:
        user_listview.update()


def create_user(e: ft.ControlEvent):
    pass


def refresh_user_list(page: ft.Page, _update_page=True):
    loading_animation.visible = True
    user_listview.visible = False
    page.update()

    response = build_request(
        page,
        action="list_users",
        data={},
        username=page.session.get("username"),
        token=page.session.get("token"),
    )
    loading_animation.visible = False
    page.update()
    if (code := response["code"]) != 200:
        send_error(page, f"加载失败: ({code}) {response['message']}")
    else:
        update_user_controls(
            response["data"]["users"], _update_page
        )
        user_listview.visible = True
        if _update_page:
            user_listview.update()


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

user_listview = ft.ListView(
    expand=True,
    visible=False,  # Initially hidden
)

manage_accounts_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("用户列表", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    ft.IconButton(ft.Icons.ADD, on_click=create_user),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=lambda e: refresh_user_list(e.page),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            ft.Divider(),
            loading_animation,
            user_listview,
        ],
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.top_center,
    visible=True,
    expand=True,
)


@route("manage")
class ManageModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    appbar = ft.AppBar(
        title=ft.Text("Management"),
        # center_title=True,
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.go("/home")
        ),
    )
    navigation_bar = ManagementNavBar()

    controls = [manage_accounts_container]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.page.session.set("refresh_user_list", refresh_user_list)
