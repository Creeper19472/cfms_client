import time
import flet as ft
from flet_model import Model, route
import flet_datatable2 as fdt
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
                label="Groups",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_APPLICATIONS, label="Settings"
            ),
            ft.NavigationBarDestination(icon=ft.Icons.ARTICLE, label="Logs"),
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
                manage_groups_container.visible = False
                manage_accounts_container.visible = True
                view_audit_logs_container.visible = False
                e.page.update()
                refresh_user_list(e.page)

            case 1:
                manage_accounts_container.visible = False
                manage_groups_container.visible = True
                view_audit_logs_container.visible = False
                e.page.update()
                refresh_group_list(e.page)
            case 3:
                manage_accounts_container.visible = False
                manage_groups_container.visible = False
                view_audit_logs_container.visible = True
                e.page.update()
                refresh_audit_logs(e.page)


def on_user_right_click_menu(e: ft.ControlEvent):
    def delete_user(inner_event: ft.ControlEvent):
        response = build_request(
            inner_event.page,
            action="delete_user",
            data={"username": e.control.data},
            username=inner_event.page.session.get("username"),
            token=inner_event.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(
                inner_event.page, f"删除用户失败: ({code}) {response['message']}"
            )
        else:
            refresh_user_list(inner_event.page)

        inner_event.page.close(dialog)

    def rename_user(inner_event: ft.ControlEvent):  # nickname
        inner_event.page.close(dialog)

        ### 弹出重命名窗口
        this_loading_animation = ft.ProgressRing(visible=False)

        def request_rename_user(secondary_inner_event: ft.ControlEvent):
            nickname_field.disabled = True
            cancel_button.disabled = True
            this_loading_animation.visible = True
            new_dialog.modal = True
            new_dialog.actions.remove(submit_button)
            inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="rename_user",
                data={
                    "username": e.control.data,
                    "nickname": nickname_field.value,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"重命名用户昵称失败: ({code}) {response['message']}",
                )
            else:
                refresh_user_list(inner_event.page)

            inner_event.page.close(new_dialog)

        nickname_field = ft.TextField(
            label="用户的新昵称", on_submit=request_rename_user
        )
        submit_button = ft.TextButton("重命名", on_click=request_rename_user)
        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(new_dialog)
        )

        new_dialog = ft.AlertDialog(
            title=ft.Text("重命名用户昵称"),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[
                    nickname_field,
                ],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
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

    def view_user_info(inner_event: ft.ControlEvent):
        dialog.open = False
        e.page.update()

        this_loading_animation = ft.ProgressRing(visible=True)

        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(info_dialog)
        )

        info_listview = ft.ListView(visible=False)

        def request_user_info(secondary_inner_event: ft.ControlEvent):

            this_loading_animation.visible = True
            info_listview.visible = False
            secondary_inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="get_user_info",
                data={
                    "username": e.control.data,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                e.page.close(info_dialog)
                send_error(
                    inner_event.page,
                    f"拉取用户信息失败: ({code}) {response['message']}",
                )
            else:
                info_listview.controls = [
                    ft.Text(f"用户名: {response['data']['username']}"),
                    ft.Text(
                        f"用户昵称: {response['data']['nickname'] if response['data']['nickname'] else '（无）'}"
                    ),
                    ft.Text(f"用户权限: {response['data']['permissions']}"),
                    ft.Text(f"用户组： {response['data']['groups']}"),
                    ft.Text(
                        f"用户注册时间: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                    ft.Text(
                        f"最后登录于: {datetime.fromtimestamp(response['data']['last_login']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                ]
                this_loading_animation.visible = False
                info_listview.visible = True

            e.page.update()

        info_dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("用户详情"),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=request_user_info,
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
        request_user_info(inner_event)

    def change_user_group(inner_event: ft.ControlEvent):
        dialog.open = False
        e.page.update()

        # 初始化列表
        dialog_group_listview = ft.ListView(expand=True)

        this_loading_animation = ft.ProgressRing(visible=False)

        def _refresh_group_list(secondary_inner_event: ft.ControlEvent):

            dialog_group_listview.disabled = True
            refresh_button.disabled = True
            e.page.update()

            # 重置列表
            dialog_group_listview.controls = []

            # 拉取用户组列表
            group_list_response = build_request(
                inner_event.page,
                action="list_groups",
                data={},
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := group_list_response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"拉取用户组列表失败: ({code}) {group_list_response['message']}",
                )
                return

            all_group_list = [
                group["name"] for group in group_list_response["data"]["groups"]
            ]

            user_data_response = build_request(
                inner_event.page,
                action="get_user_info",
                data={
                    "username": e.control.data,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := user_data_response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"拉取用户信息失败: ({code}) {user_data_response['message']}",
                )
                return
            user_membership_list = user_data_response["data"]["groups"]

            for each_group in all_group_list:
                dialog_group_listview.controls.append(
                    ft.Checkbox(
                        label=each_group,  # 后面可能改成显示名称
                        data=each_group,
                        on_change=None,  # 提交前什么都不处理
                        value=each_group in user_membership_list,
                    )
                )

            dialog_group_listview.disabled = False
            refresh_button.disabled = False
            e.page.update()

        def _submit_group_changes(secondary_inner_event: ft.ControlEvent):

            dialog_group_listview.disabled = True
            dialog_group_listview.update()

            # ... "data": {"latest": []}
            # 提交更改后所有勾选的用户组
            to_submit_list = []
            for checkbox in dialog_group_listview.controls:
                assert isinstance(checkbox, ft.Checkbox)
                if checkbox.value == True:
                    to_submit_list.append(checkbox.data)

            response = build_request(
                inner_event.page,
                action="change_user_groups",
                data={
                    "username": e.control.data,
                    "groups": to_submit_list,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"更改用户组失败: ({code}) {response['message']}",
                )
            else:
                refresh_user_list(inner_event.page)

            e.page.close(change_dialog)

        submit_button = ft.TextButton("提交", on_click=_submit_group_changes)
        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(change_dialog)
        )
        refresh_button = ft.IconButton(
            ft.Icons.REFRESH,
            on_click=_refresh_group_list,
        )

        change_dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("更改用户组"),
                    refresh_button,
                ]
            ),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[this_loading_animation, dialog_group_listview],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                submit_button,
                cancel_button,
            ],
            # scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(change_dialog)
        _refresh_group_list(inner_event)

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
                        leading=ft.Icon(ft.Icons.FORMAT_LIST_BULLETED),
                        title=ft.Text("编辑用户组"),
                        subtitle=ft.Text(f"为用户更改所属的用户组"),
                        on_click=change_user_group,
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
        content=ft.Column(
            [menu_listview], width=400, scroll=ft.ScrollMode.AUTO, expand=True
        ),
        # scrollable=True,
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
                    title=ft.Text(
                        user["nickname"] if user["nickname"] else user["username"]
                    ),
                    subtitle=ft.Text(
                        f"{user["groups"]}\n"
                        + f"Last login: {datetime.fromtimestamp(user['last_login']).strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else "Unknown"}"
                    ),
                    is_three_line=True,
                    data=user["username"],
                    on_click=on_user_right_click_menu,
                ),
                data=user["username"],
                on_secondary_tap=on_user_right_click_menu,
                on_long_press_start=on_user_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for user in users
        ]
    )
    if _update_page:
        user_listview.update()


def open_create_user_form(e: ft.ControlEvent):
    def request_create_user(inner_event: ft.ControlEvent):
        this_loading_animation.visible = True
        inner_event.page.update()

        username_field.disabled = True
        nickname_field.disabled = True
        password_field.disabled = True

        cancel_button.disabled = True
        this_loading_animation.visible = True
        dialog.modal = True
        dialog.actions.remove(submit_button)
        inner_event.page.update()

        response = build_request(
            inner_event.page,
            action="create_user",
            data={
                "username": username_field.value,
                "password": password_field.value,
                "nickname": nickname_field.value,
                "permissions": [],  # TODO
                "groups": [],
            },
            username=e.page.session.get("username"),
            token=e.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(
                inner_event.page, f"创建用户失败: ({code}) {response['message']}"
            )
        else:
            refresh_user_list(inner_event.page)

        inner_event.page.close(
            dialog
        )  # 反正要关闭对话框，那么是否要恢复 .disabled = False 都无所谓了

    this_loading_animation = ft.ProgressRing(visible=False)

    password_field = ft.TextField(
        label="密码",
        password=True,
        can_reveal_password=True,
        on_submit=request_create_user,
    )
    nickname_field = ft.TextField(
        label="昵称", on_submit=lambda _: password_field.focus()
    )
    username_field = ft.TextField(
        label="用户名", on_submit=lambda _: nickname_field.focus()
    )

    submit_button = ft.TextButton(
        "创建",
        on_click=request_create_user,
    )
    cancel_button = ft.TextButton("取消", on_click=lambda e: e.page.close(dialog))

    dialog = ft.AlertDialog(
        title=ft.Text("创建用户"),
        # title_padding=ft.padding.all(25),
        content=ft.Column(
            controls=[username_field, nickname_field, password_field],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
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

    e.page.open(dialog)


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
        update_user_controls(response["data"]["users"], _update_page)
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
                    ft.IconButton(ft.Icons.ADD, on_click=open_create_user_form),
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


def open_create_group_form(e: ft.ControlEvent):
    def request_create_group(inner_event: ft.ControlEvent):
        this_loading_animation.visible = True
        inner_event.page.update()

        group_name_field.disabled = True
        display_name_field.disabled = True
        cancel_button.disabled = True
        this_loading_animation.visible = True
        dialog.modal = True
        dialog.actions.remove(submit_button)
        inner_event.page.update()

        response = build_request(
            inner_event.page,
            action="create_group",
            data={
                "group_name": group_name_field.value,
                "display_name": display_name_field.value,
                "permissions": [],  # TODO
            },
            username=e.page.session.get("username"),
            token=e.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(
                inner_event.page, f"创建用户组失败: ({code}) {response['message']}"
            )
        else:
            refresh_group_list(inner_event.page)

        inner_event.page.close(dialog)

    this_loading_animation = ft.ProgressRing(visible=False)

    display_name_field = ft.TextField(label="展示名称", on_submit=request_create_group)
    group_name_field = ft.TextField(
        label="用户组名称", on_submit=lambda _: display_name_field.focus()
    )

    submit_button = ft.TextButton(
        "创建",
        on_click=request_create_group,
    )
    cancel_button = ft.TextButton("取消", on_click=lambda e: e.page.close(dialog))

    dialog = ft.AlertDialog(
        title=ft.Text("创建用户组"),
        # title_padding=ft.padding.all(25),
        content=ft.Column(
            controls=[group_name_field, display_name_field],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
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

    e.page.open(dialog)


group_listview = ft.ListView(
    expand=True,
    visible=False,  # Initially hidden
)


manage_groups_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("用户组列表", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    ft.IconButton(
                        ft.Icons.GROUP_ADD_OUTLINED, on_click=open_create_group_form
                    ),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=lambda e: refresh_group_list(e.page),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            ft.Divider(),
            loading_animation,
            group_listview,
        ],
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.top_center,
    visible=False,
    expand=True,
)


def on_group_right_click_menu(e: ft.ControlEvent):
    def delete_group(inner_event: ft.ControlEvent):
        response = build_request(
            inner_event.page,
            action="delete_group",
            data={"group_name": e.control.data},
            username=inner_event.page.session.get("username"),
            token=inner_event.page.session.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(
                inner_event.page, f"删除用户组失败: ({code}) {response['message']}"
            )
        else:
            refresh_group_list(inner_event.page)

        inner_event.page.close(dialog)

    def rename_group(inner_event: ft.ControlEvent):  # nickname
        inner_event.page.close(dialog)

        ### 弹出重命名窗口
        this_loading_animation = ft.ProgressRing(visible=False)

        def request_rename_group(secondary_inner_event: ft.ControlEvent):
            display_name_field.disabled = True
            cancel_button.disabled = True
            this_loading_animation.visible = True
            new_dialog.modal = True
            new_dialog.actions.remove(submit_button)
            inner_event.page.update()

            response = build_request(
                inner_event.page,
                action="rename_group",
                data={
                    "group_name": e.control.data,
                    "display_name": display_name_field.value,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"重命名用户组失败: ({code}) {response['message']}",
                )
            else:
                refresh_group_list(inner_event.page)

            inner_event.page.close(new_dialog)

        display_name_field = ft.TextField(
            label="用户组的新名称", on_submit=request_rename_group
        )
        submit_button = ft.TextButton("重命名", on_click=request_rename_group)
        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(new_dialog)
        )

        new_dialog = ft.AlertDialog(
            title=ft.Text("重命名用户组"),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[
                    display_name_field,
                ],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
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

    def set_group_permissions(inner_event: ft.ControlEvent):
        # return
        dialog.open = False
        e.page.update()

        # 初始化列表
        dialog_permission_listview = ft.ListView(expand=True)

        this_loading_animation = ft.ProgressRing(visible=False)

        def _refresh_permission_list(secondary_inner_event: ft.ControlEvent):

            dialog_permission_listview.disabled = True
            refresh_button.disabled = True
            e.page.update()

            # 重置列表
            dialog_permission_listview.controls = []

            # 拉取用户组信息
            group_info_response = build_request(
                inner_event.page,
                action="get_group_info",
                data={"group_name": e.control.data},
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := group_info_response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"拉取用户组信息失败: ({code}) {group_info_response['message']}",
                )
                return

            all_permission_list = group_info_response["data"]["permissions"]

            for each_permission in all_permission_list:
                dialog_permission_listview.controls.append(
                    ft.Checkbox(
                        label=each_permission,  # 后面可能改成显示名称
                        data=each_permission,
                        on_change=None,  # 提交前什么都不处理
                        value=each_permission in all_permission_list,
                    )
                )

            dialog_permission_listview.disabled = False
            refresh_button.disabled = False
            e.page.update()

        def _submit_group_changes(secondary_inner_event: ft.ControlEvent):

            dialog_permission_listview.disabled = True
            dialog_permission_listview.update()

            # ... "data": {"latest": []}
            # 提交更改后所有勾选的用户组
            to_submit_list = []
            for checkbox in dialog_permission_listview.controls:
                assert isinstance(checkbox, ft.Checkbox)
                if checkbox.value == True:
                    to_submit_list.append(checkbox.data)

            response = build_request(
                inner_event.page,
                action="change_group_permissions",
                data={
                    "group_name": e.control.data,
                    "permissions": to_submit_list,
                },
                username=e.page.session.get("username"),
                token=e.page.session.get("token"),
            )
            if (code := response["code"]) != 200:
                send_error(
                    inner_event.page,
                    f"更改用户组权限失败: ({code}) {response['message']}",
                )
            else:
                refresh_group_list(inner_event.page)

            e.page.close(change_dialog)

        submit_button = ft.TextButton("提交", on_click=_submit_group_changes)
        cancel_button = ft.TextButton(
            "取消", on_click=lambda _: inner_event.page.close(change_dialog)
        )
        refresh_button = ft.IconButton(
            ft.Icons.REFRESH,
            on_click=_refresh_permission_list,
        )

        def _add_permission(secondary_inner_event: ft.ControlEvent):
            if not add_textfield.value:
                return

            if add_textfield.value not in [
                control.data for control in dialog_permission_listview.controls
            ]:
                dialog_permission_listview.controls.append(
                    ft.Checkbox(
                        label=add_textfield.value,
                        data=add_textfield.value,
                        on_change=None,  # 提交前什么都不处理
                        value=True,  # 默认选中
                        # autofocus=True,
                    )
                )

            add_textfield.value = None
            secondary_inner_event.page.update()
            _update_add_button(secondary_inner_event)

        def _update_add_button(secondary_inner_event: ft.ControlEvent):
            add_button.disabled = not add_textfield.value
            secondary_inner_event.page.update()

        add_textfield = ft.TextField(
            label="新增权限",
            on_submit=_add_permission,
            expand=True,
            on_change=_update_add_button,
        )
        add_button = ft.IconButton(
            ft.Icons.ADD, on_click=_add_permission, disabled=True
        )

        change_dialog = ft.AlertDialog(
            title=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("更改用户组权限"),
                            refresh_button,
                        ]
                    ),
                    ft.Row(controls=[add_button, add_textfield]),
                ]
            ),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[this_loading_animation, dialog_permission_listview],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                auto_scroll=True,
            ),
            actions=[
                submit_button,
                cancel_button,
            ],
            # scrollable=True,
            # alignment=ft.MainAxisAlignment.CENTER,
        )

        inner_event.page.open(change_dialog)
        _refresh_permission_list(inner_event)

    menu_listview = ft.ListView(
        controls=[
            ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.GROUP_REMOVE),
                        title=ft.Text("删除"),
                        subtitle=ft.Text(f"删除此用户组"),
                        on_click=delete_group,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                        title=ft.Text("重命名"),
                        subtitle=ft.Text(f"为用户组更改展示的名称"),
                        on_click=rename_group,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED),
                        title=ft.Text("设置权限"),
                        subtitle=ft.Text(f"为用户组更改拥有的权限"),
                        on_click=set_group_permissions,
                    ),
                ],
            )
        ]
    )

    dialog = ft.AlertDialog(
        title=ft.Text("操作"),
        content=ft.Column(
            [menu_listview], width=400, scroll=ft.ScrollMode.AUTO, expand=True
        ),
        # scrollable=True,
        alignment=ft.alignment.center,
    )

    e.page.open(dialog)
    e.page.update()


def update_group_controls(groups: list[dict], _update_page=True):
    group_listview.controls = []  # reset
    group_listview.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.GROUPS_3),
                    title=ft.Text(
                        group["display_name"]
                        if group["display_name"]
                        else group["name"]
                    ),
                    subtitle=ft.Text(
                        f"Permissions: {group["permissions"]}\n"
                        + f"Members: {group['members']}"
                    ),
                    is_three_line=True,
                    data=group["name"],
                    on_click=on_group_right_click_menu,
                ),
                data=group["name"],
                on_secondary_tap=on_group_right_click_menu,
                on_long_press_start=on_group_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for group in groups
        ]
    )
    if _update_page:
        group_listview.update()


def refresh_group_list(page: ft.Page, _update_page=True):
    loading_animation.visible = True
    group_listview.visible = False
    page.update()

    response = build_request(
        page,
        action="list_groups",
        data={},
        username=page.session.get("username"),
        token=page.session.get("token"),
    )
    loading_animation.visible = False
    page.update()
    if (code := response["code"]) != 200:
        send_error(page, f"加载失败: ({code}) {response['message']}")
    else:
        update_group_controls(response["data"]["groups"], _update_page)
        group_listview.visible = True
        if _update_page:
            group_listview.update()


def apply_lockdown(event: ft.ControlEvent):
    # 事先更新用户数据
    user_data_response = build_request(
        event.page,
        action="get_user_info",
        data={
            "username": event.page.session.get("username"),
        },
        username=event.page.session.get("username"),
        token=event.page.session.get("token"),
    )
    event.page.session.set("nickname", user_data_response["data"].get("nickname"))
    event.page.session.set(
        "user_permissions", user_data_response["data"]["permissions"]
    )
    event.page.session.set("user_groups", user_data_response["data"]["groups"])

    status = not event.page.session.get("lockdown")

    response = build_request(
        event.page,
        "lockdown",
        {"status": status},
        username=event.page.session.get("username"),
        token=event.page.session.get("token"),
    )
    if response["code"] != 200:
        send_error(event.page, f"锁闭失败: ({response["code"]}) {response['message']}")
        return

    event.page.session.set("lockdown", status)
    return


def select_row(e: ft.ControlEvent):
    print("on_select_row")
    e.control.selected = not e.control.selected
    e.control.update()


def sort_column(e: ft.DataColumnSortEvent):
    print(f"Sorting column {e.column_index}, ascending={e.ascending}")


def all_selected(e: ft.ControlEvent):
    print("All selected")


audit_logs_datatable = fdt.DataTable2(
    # heading_row_color=ft.Colors.SECONDARY_CONTAINER,
    horizontal_margin=12,
    data_row_height=60,
    sort_ascending=True,
    on_select_all=all_selected,
    sort_column_index=7,
    bottom_margin=10,
    min_width=600,
    columns=[
        fdt.DataColumn2(
            ft.Text("ID"),
            size=fdt.Size.L,
            heading_row_alignment=ft.MainAxisAlignment.START,
            on_sort=sort_column,  # type: ignore
        ),
        fdt.DataColumn2(ft.Text("Action")),
        fdt.DataColumn2(ft.Text("Username")),
        fdt.DataColumn2(
            ft.Text("Target"),
            size=fdt.Size.L,
        ),
        fdt.DataColumn2(
            ft.Text("Data"),
            size=fdt.Size.M,
        ),
        fdt.DataColumn2(ft.Text("Result"), size=fdt.Size.S, numeric=True),
        fdt.DataColumn2(ft.Text("Remote Address"), size=fdt.Size.M),
        fdt.DataColumn2(ft.Text("Time"), numeric=True, size=fdt.Size.M),
    ],
    rows=[],
    expand=True,
    visible=False,
)


def refresh_audit_logs(page: ft.Page):

    def update_audit_logs_controls(entries: list[dict]):
        assert type(audit_logs_datatable.rows) is list

        audit_logs_datatable.rows.clear()

        audit_logged_actions = set()
        for entry in entries:
            audit_logs_datatable.rows.append(
                fdt.DataRow2(
                    cells=[
                        ft.DataCell(ft.Text(entry["id"])),
                        ft.DataCell(ft.Text(entry["action"])),
                        ft.DataCell(ft.Text(entry["username"])),
                        ft.DataCell(ft.Text(entry["target"])),
                        ft.DataCell(
                            ft.Text(str(entry["data"]) if entry["data"] else None)
                        ),
                        ft.DataCell(ft.Text(entry["result"])),
                        ft.DataCell(ft.Text(entry["remote_address"])),
                        ft.DataCell(
                            ft.Text(
                                datetime.fromtimestamp(entry["logged_time"]).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                            )
                        ),
                    ]
                )
            )
            audit_logged_actions.add(entry["action"])

        # c1 = time.time()

        audit_action_segmented_button_ref.current.segments.clear()
        for action in audit_logged_actions:
            audit_action_segmented_button_ref.current.segments.append(
                ft.Segment(
                    value=action,
                    label=ft.Text(action),
                    icon=ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK),
                )
            )

        audit_action_segmented_button_ref.current.selected = audit_logged_actions
        audit_action_segmented_button_ref.current.update()

        # c2 = time.time()
        # print(c2-c1)

    loading_animation.visible = True
    audit_logs_datatable.visible = False
    page.update()

    response = build_request(
        page,
        action="view_audit_logs",
        data={"offset": audit_view_offset, "count": audit_view_count},
        username=page.session.get("username"),
        token=page.session.get("token"),
    )
    loading_animation.visible = False
    page.update()
    if (code := response["code"]) != 200:
        send_error(page, f"加载失败: ({code}) {response['message']}")
    else:
        view_start = audit_view_offset + 1
        view_end = audit_view_offset + audit_view_count
        if view_end > response["data"]["total"]:
            view_end = response["data"]["total"]
        audit_info_ref.current.value = f"{view_start} - {view_end} 条，共 {response["data"]["total"]} 条"
        audit_info_ref.current.update()
        audit_navigate_before_ref.current.disabled = audit_view_offset <= 0
        audit_navigate_before_ref.current.update()
        audit_navigate_next_ref.current.disabled = (
            audit_view_offset + audit_view_count >= response["data"]["total"]
        )
        audit_navigate_next_ref.current.update()
        update_audit_logs_controls(response["data"]["entries"])
        audit_logs_datatable.visible = True
        audit_logs_datatable.update()


def audit_view_navigate_before_pressed(event: ft.ControlEvent):
    global audit_view_offset
    audit_view_offset -= audit_view_count
    if audit_view_offset < 0:
        audit_view_offset = 0
    refresh_audit_logs(event.page)


def audit_view_navigate_next_pressed(event: ft.ControlEvent):
    global audit_view_offset
    audit_view_offset += audit_view_count
    refresh_audit_logs(event.page)


audit_info_ref = ft.Ref[ft.Text]()
audit_navigate_before_ref = ft.Ref[ft.IconButton]()
audit_navigate_next_ref = ft.Ref[ft.IconButton]()
audit_action_segmented_button_ref = ft.Ref[ft.SegmentedButton]()
audit_view_offset = 0
audit_view_count = 100
# audit_logged_actions = {
#     "login",
#     "get_document",
#     "create_document",
#     "upload_document",
#     "delete_document",
#     "rename_document",
#     "move_document",
#     "get_document_info",
#     "set_document_rules",
#     "list_directory",
#     "get_directory_info",
#     "create_directory",
#     "delete_directory",
#     "rename_directory",
#     "move_directory",
#     "list_users",
#     ""
# }

view_audit_logs_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("审计日志", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=lambda e: refresh_audit_logs(e.page),
                    ),
                    ft.IconButton(
                        ft.Icons.NAVIGATE_BEFORE,
                        on_click=audit_view_navigate_before_pressed,
                        ref=audit_navigate_before_ref,
                    ),
                    ft.IconButton(
                        ft.Icons.NAVIGATE_NEXT,
                        on_click=audit_view_navigate_next_pressed,
                        ref=audit_navigate_next_ref,
                    ),
                    ft.Text(ref=audit_info_ref),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            ft.SegmentedButton(
                [
                    ft.Segment(
                        value="all",
                        label=ft.Text("全部"),
                        icon=ft.Icon(ft.Icons.ALL_INBOX),
                    )
                ],
                selected={"all"},
                allow_empty_selection=False,
                allow_multiple_selection=True,
                ref=audit_action_segmented_button_ref,
            ),
            ft.Divider(),
            loading_animation,
            audit_logs_datatable,
        ],
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.top_center,
    visible=False,
    expand=True,
)


@route("manage")
class ManageModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    _leading_ref = ft.Ref[ft.IconButton]()

    appbar = ft.AppBar(
        title=ft.Text("Management"),
        # center_title=True,
        leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, ref=_leading_ref),
    )
    navigation_bar = ManagementNavBar()

    _fab_ref = ft.Ref[ft.FloatingActionButton]()
    floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.LOCK, on_click=apply_lockdown, ref=_fab_ref
    )
    floating_action_button_location = "endFloat"

    controls = [
        manage_accounts_container,
        manage_groups_container,
        view_audit_logs_container,
    ]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.page.session.set("refresh_user_list", refresh_user_list)

    def _go_back(self, event: ft.ControlEvent):
        self.page.views.pop()
        if last_route := self.page.views[-1].route:
            self.page.go(last_route)

    def post_init(self) -> None:
        self._leading_ref.current.on_click = self._go_back
        self._leading_ref.current.update()
        self._fab_ref.current.visible = "apply_lockdown" in self.page.session.get("user_permissions")  # type: ignore
        self._fab_ref.current.update()
