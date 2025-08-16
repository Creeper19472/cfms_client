from typing import Optional
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection
from include.request import build_request
from common.notifications import send_error


def open_change_passwd_dialog(e: ft.ControlEvent, tip: Optional[str] = None):

    def request_set_passwd(inner_event: ft.ControlEvent):
        
        this_loading_animation.visible = True
        old_passwd_field.disabled = True
        new_passwd_field.disabled = True
        cancel_button.disabled = True
        dialog.actions.remove(submit_button)
        inner_event.page.update()
        
        response = build_request(
            inner_event.page,
            "set_passwd",
            data={
                "username": e.page.session.get("username"),
                "old_passwd": old_passwd_field.value,
                "new_passwd": new_passwd_field.value,
            }, # 修改密码，无需 data 外提供 username 和 token
        )

        inner_event.page.close(dialog)

        if response["code"] != 200:
            send_error(inner_event.page, f"修改密码失败: {response['message']}")
        else:
            if inner_event.page.platform.value not in ["ios", "android"]:
                inner_event.page.window.close()
            else:
                send_error(inner_event.page, "您已登出，请手动重启应用")


    this_loading_animation = ft.ProgressRing(visible=False)

    new_passwd_field = ft.TextField(
        label="新密码",
        on_submit=request_set_passwd,
        password=True,
        can_reveal_password=True,
    )
    old_passwd_field = ft.TextField(
        label="旧密码",
        on_submit=lambda _: new_passwd_field.focus(),
        password=True,
        can_reveal_password=True,
    )
    
    submit_button = ft.ElevatedButton(
        "修改",
        on_click=request_set_passwd,
    )
    cancel_button = ft.TextButton("取消", on_click=lambda e: e.page.close(dialog))

    tip_ref = ft.Ref[ft.Text]()

    dialog = ft.AlertDialog(
        title=ft.Text("修改密码"),
        content=ft.Column(
            controls=[
                old_passwd_field,
                new_passwd_field,
                ft.Text(tip, ref=tip_ref, text_align=ft.TextAlign.CENTER)
            ],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            submit_button,
            this_loading_animation,
            cancel_button,
        ],
        # scrollable=True,
    )

    tip_ref.current.visible = bool(tip)
    e.page.open(dialog)


@route("settings")
class SettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    _leading_ref = ft.Ref[ft.IconButton]()

    appbar = ft.AppBar(
        title=ft.Text("Settings"),
        # center_title=True,
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK, ref=_leading_ref
        ),
    )

    listtiles = [
        ft.ListTile(
            leading=ft.Icon(ft.Icons.PASSWORD),
            title=ft.Text("修改密码"),
            on_click=open_change_passwd_dialog,
        ),
    ]

    listview = ft.ListView(
        expand=True, padding=10, auto_scroll=True, controls=listtiles
    )

    controls = [listview]

    def __init__(self, page: ft.Page):
        super().__init__(page)

    def _go_back(self, event: ft.ControlEvent):
        self.page.views.pop()
        if last_route := self.page.views[-1].route:
            self.page.go(last_route)

    def post_init(self) -> None:
        self._leading_ref.current.on_click = self._go_back
        self._leading_ref.current.update()
