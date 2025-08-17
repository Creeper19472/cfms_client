from typing import Optional
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection
from include.request import build_request
from common.notifications import send_error


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
        leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, ref=_leading_ref),
    )

    listtiles = [
        ft.ListTile(
            leading=ft.Icon(ft.Icons.SECURITY),
            title=ft.Text("安全"),
            subtitle=ft.Text("更改应用的安全设置"),
            # on_click=open_change_passwd_dialog,
        ),
        ft.ListTile(
            leading=ft.Icon(ft.Icons.NETWORK_WIFI_2_BAR_OUTLINED),
            title=ft.Text("连接"),
            subtitle=ft.Text("更改应用使用代理的规则"),
            # on_click=open_change_passwd_dialog,
        ),
        ft.ListTile(
            leading=ft.Icon(ft.Icons.BROWSER_UPDATED),
            title=ft.Text("更新"),
            subtitle=ft.Text("自动检查和安装更新"),
            # on_click=open_change_passwd_dialog,
        ),
    ]

    listview = ft.ListView(
        expand=True,
        padding=10,
        auto_scroll=True,
        controls=listtiles,
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
