# type: ignore
import flet as ft
from flet_model import Model, route
import re
from websockets.sync.client import connect
import ssl, json, os
from flet_permission_handler import (
    PermissionHandler,
    PermissionStatus,
    PermissionType,
)
from common.notifications import send_error
from include.request import build_request
from include.listener import listen_to_server, server_info_updater
import threading

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


def build_error_bar(message: str = None, duration=4.0):
    return ft.SnackBar(
        content=ft.Text(message),
        show_close_icon=True,
        duration=duration,
        behavior=ft.SnackBarBehavior.FLOATING,
        bgcolor=ERROR_COLOR,
    )


@route("connect")
class ConnectToServerModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    appbar = ft.AppBar(title=ft.Text("Connect to Server"), center_title=True)

    floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.BROWSER_UPDATED_OUTLINED,
        on_click=lambda event: event.page.go("/connect/about"),
        tooltip="检查更新",
    )
    floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

    def connect_button_clicked(self, e):
        self.connect_button.visible = False
        self.loading_animation.visible = True
        self.input_text_field.disabled = True
        self.page.update()

        server_address = "wss://" + self.server_address_ref.current.value
        # print(server_address)
        # Regular expression to match "wss://<valid server address>"
        wss_pattern_v4 = r"^wss:\/\/[a-zA-Z0-9.-]+(:[0-9]+)?$"
        wss_pattern_v6 = r"^wss:\/\/\[(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}|:(?::[0-9a-fA-F]{1,4}){1,7})\](?::[0-9]{1,5})?$"
        wss_pattern = wss_pattern_v4 + "|" + wss_pattern_v6

        # Check if the server address matches the pattern
        if not server_address or not re.match(wss_pattern, server_address):
            self.connect_button.visible = True
            self.loading_animation.visible = False
            self.input_text_field.disabled = False
            self.error_bar.content.value: str = "无效的服务器地址"
            self.page.update()
            self.page.open(self.error_bar)
            return  # Exit the function if the pattern is invalid
        else:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            try:
                self.page.session.set(
                    "websocket", connect(server_address, ssl=ssl_context)
                )
            except Exception as e:
                self.connect_button.visible = True
                self.loading_animation.visible = False
                self.input_text_field.disabled = False
                self.error_bar.content.value: str = f"连接失败：{e}"
                self.page.update()
                self.page.open(self.error_bar)
                return

            server_info_response = build_request(self.page, "server_info")
            if (
                server_protocol_version := server_info_response["data"][
                    "protocol_version"
                ]
            ) > self.page.session.get("protocol_version"):
                self.page.session.get("websocket").close()
                self.page.session.set("websocket", None)
                self.connect_button.visible = True
                self.loading_animation.visible = False
                self.input_text_field.disabled = False
                self.error_bar.content.value: str = (
                    f"您正在连接到一个使用更高版本协议的服务器（协议版本 {server_protocol_version}），请更新客户端。"
                )
                self.page.update()
                self.page.open(self.error_bar)
                return

            self.page.session.set("server_info", server_info_response["data"])
            self.page.session.set("server_uri", server_address)
            self.page.title = f"CFMS Client - {server_address}"

            # set listener
            listener_thread = threading.Thread(
                target=listen_to_server,
                args=(
                    self.page,
                    server_address,
                ),
                daemon=True,
            )
            listener_thread.start()

            # set updater
            updater_thread = threading.Thread(
                target=server_info_updater,
                args=(
                    self.page,
                    server_address,
                ),
                daemon=True,
            )
            updater_thread.start()

            # self.ph.request_permission(PermissionType.ACCESS_MEDIA_LOCATION)
            # self.ph.request_permission(PermissionType.STORAGE)
            if (
                self.ph.request_permission(PermissionType.MANAGE_EXTERNAL_STORAGE)
                == PermissionStatus.DENIED
            ):
                if self.page.platform.value not in ["ios", "android"]:
                    self.page.window.close()
                else:
                    send_error(
                        self.page,
                        "授权失败，您将无法正常下载文件。请在设置中允许应用访问您的文件。",
                    )

            if self.page.platform.value == "windows" and os.environ.get(
                "FLET_APP_CONSOLE"
            ):
                os.startfile(os.getcwd())

            self.page.go("/login")

    def __init__(self, page: ft.Page):
        super().__init__(page)

        # Refs
        self.server_address_ref = ft.Ref[ft.TextField]()
        self.form_container_ref = ft.Ref[ft.Container]()

        self.connect_button = ft.ElevatedButton(
            text="连接",
            bgcolor=PRIMARY_COLOR,
            color=TEXT_COLOR,
            on_click=self.connect_button_clicked,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BUTTON_RADIUS)),
        )

        self.loading_animation = ft.ProgressRing(visible=False)

        self.error_bar = build_error_bar()
        self.input_text_field = ft.TextField(
            ref=self.server_address_ref,
            label="服务器地址",
            # prefix_icon=ft.Icons.MONITOR_OUTLINED,
            # prefix_icon_size_constraints=,
            prefix_text="wss://",
            hint_text="e.g. localhost:5104",
            border_color=BORDER_COLOR,
            cursor_color=PRIMARY_COLOR,
            focused_border_color=PRIMARY_COLOR,
            bgcolor=FIELD_BG,
            color=TEXT_COLOR,
            hint_style=ft.TextStyle(color=PLACEHOLDER_COLOR),
            border_radius=8,
            value="localhost:5104",  # default
            autofocus=True,
            on_submit=self.connect_button_clicked,  # Listen for the enter key event
        )

        container = ft.Container(
            ref=self.form_container_ref,
            width=FORM_WIDTH,
            bgcolor=FIELD_BG,
            border_radius=BUTTON_RADIUS,
            padding=20,
            content=ft.Column(
                controls=[
                    self.input_text_field,
                    ft.Row(
                        controls=[
                            self.connect_button,
                            self.loading_animation,  # Add the loading animation next to the button
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                spacing=15,
            ),
        )

        explanation_text = ft.Text(
            self.page.session.get("version"),  # "0.0.3.20250627_alpha"
            color=PLACEHOLDER_COLOR,
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        version_container = ft.Container(
            ref=self.form_container_ref,
            content=explanation_text,
            alignment=ft.alignment.bottom_center,
        )

        self.ph = PermissionHandler()
        page.overlay.append(self.ph)
        page.session.set("ph", self.ph)

        self.controls = [container, version_container]
