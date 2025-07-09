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
                manage_groups_container.visible = False
                manage_accounts_container.visible = True
                e.page.update()
                refresh_user_list(e.page)

            case 1:
                manage_accounts_container.visible = False
                manage_groups_container.visible = True
                e.page.update()
                refresh_group_list(e.page)
            # case 2:
            #     manage_accounts_container.visible = False
            #     home_container.visible = False
            #     self.page.update()


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
            ),
            actions=[
                cancel_button,
            ],
            scrollable=True,
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
                        label=each_group, # 后面可能改成显示名称
                        data=each_group,
                        on_change=None, # 提交前什么都不处理
                        value=each_group in user_membership_list,
                    )
                )

            e.page.update()

        def _submit_group_changes(secondary_inner_event: ft.ControlEvent):
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

        change_dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("更改用户组"),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        on_click=_refresh_group_list,
                    ),
                ]
            ),
            # title_padding=ft.padding.all(25),
            content=ft.Column(
                controls=[this_loading_animation, dialog_group_listview],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            actions=[
                submit_button,
                cancel_button,
            ],
            scrollable=True,
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

        inner_event.page.close(dialog)

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
        ),
        actions=[
            submit_button,
            this_loading_animation,
            cancel_button,
        ],
        scrollable=True,
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
        ),
        actions=[
            submit_button,
            this_loading_animation,
            cancel_button,
        ],
        scrollable=True,
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

    controls = [manage_accounts_container, manage_groups_container]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.page.session.set("refresh_user_list", refresh_user_list)
