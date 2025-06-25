# type: ignore
import flet as ft
from flet_model import Model, route
import re
from websockets.sync.client import connect
import ssl, json

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

    def connect_button_clicked(self, e):
        self.connect_button.visible = False
        self.loading_animation.visible = True
        self.input_text_field.disabled = True
        self.page.update()

        server_address = self.server_address_ref.current.value
        # print(server_address)
        # Regular expression to match "wss://<valid server address>"
        wss_pattern = r"^wss:\/\/[a-zA-Z0-9.-]+(:[0-9]+)?$"

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
                self.page.websocket = connect(server_address, ssl=ssl_context)
            except Exception as e:
                self.connect_button.visible = True
                self.loading_animation.visible = False
                self.input_text_field.disabled = False
                self.error_bar.content.value: str = f"连接失败：{e}"
                self.page.update()
                self.page.open(self.error_bar)
                return

            self.page.title = f"CFMS Client - {server_address}"
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
            hint_text="e.g. wss://localhost:5104",
            border_color=BORDER_COLOR,
            cursor_color=PRIMARY_COLOR,
            focused_border_color=PRIMARY_COLOR,
            bgcolor=FIELD_BG,
            color=TEXT_COLOR,
            hint_style=ft.TextStyle(color=PLACEHOLDER_COLOR),
            border_radius=8,
            value="wss://localhost:5104", # default
            autofocus=True,
            on_submit=self.connect_button_clicked  # Listen for the enter key event
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
            "CFMS Client ver. 20250625",
            color=PLACEHOLDER_COLOR,
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        version_container = ft.Container(
            ref=self.form_container_ref,
            content=explanation_text,
            alignment=ft.alignment.bottom_center,
        )

        self.controls = [container, version_container]