# type: ignore
import flet as ft
from flet_model import Model, route
import ssl, json, time
from common.navigation import MyNavBar
from include.request import build_request
from pages.interface.passwd import open_change_passwd_dialog
import threading, logging, asyncio

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


@route("login")
class LoginModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    # UI Components

    form_container_ref = ft.Ref[ft.Container]()
    loading_animation = ft.ProgressRing(visible=False)

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            on_submit=self.request_login,
        )
        self.username_field = ft.TextField(
            label="Username",
            autofocus=True,
            on_submit=lambda e: self.password_field.focus(),
        )

        self._server_info = {}

        self.error_bar = ft.SnackBar(
            content=ft.Text(),
            show_close_icon=True,
            duration=4.0,
            behavior=ft.SnackBarBehavior.FLOATING,
            bgcolor=ERROR_COLOR,
        )

        self.login_button = ft.ElevatedButton(
            text="Login",
            bgcolor=PRIMARY_COLOR,
            color=TEXT_COLOR,
            on_click=self.request_login,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BUTTON_RADIUS)),
        )

        self.welcome_text = ft.Text(
            size=24,
            text_align=ft.TextAlign.CENTER,
            color=TEXT_COLOR,
            weight=ft.FontWeight.BOLD,
        )

        # required_cred_dlg =

        container = ft.Container(
            ref=self.form_container_ref,
            width=FORM_WIDTH,
            bgcolor=FIELD_BG,
            border_radius=BUTTON_RADIUS,
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("Login", size=24),
                    ft.Column(
                        controls=[
                            self.username_field,
                            self.password_field,
                            ft.Row(
                                controls=[
                                    self.login_button,
                                    self.loading_animation,
                                    # ft.OutlinedButton(text="Sign Up", on_click=None),
                                ]
                            ),
                        ]
                    ),
                ],
                spacing=15,
            ),
        )

        self.controls = [self.welcome_text, container]

    def post_init(self) -> None:
        self._server_info: dict = self.page.session.get("server_info")
        self.welcome_text.value = (
            f"{self._server_info.get('server_name', 'CFMS Server')}"
        )
        self.page.update()

    def request_login(self, e):

        self.login_button.visible = False
        self.loading_animation.visible = True
        self.username_field.disabled = True
        self.password_field.disabled = True
        self.update()

        if self.username_field.value == "" or self.password_field.value == "":
            # empty fields show error
            self.login_button.visible = True
            self.loading_animation.visible = False
            self.username_field.disabled = False
            self.password_field.disabled = False

            self.update()
            self.error_bar.content.value = "Username and Password cannot be empty"
            self.page.open(self.error_bar)

        else:
            """
            Send request and handle response here
            use utils.build_request or utils.async_build_request to send your requests

            data = {"username": self.username_field.value, "password": self.password_field.value}
            login_resp = build_request(self.page, YOUR_FULL_LOGIN_URL, data, authenticated=False)
            token = json.loads(login_resp.text)

            #save the token to client storage (refresh and access tokens)
            for k in token:
                self.page.client_storage.set(k, token[k])
            """

            response = build_request(
                self.page,
                "login",
                {
                    "username": self.username_field.value,
                    "password": self.password_field.value,
                },
            )

            if (code := response["code"]) == 200:
                self.page.session.set("username", self.username_field.value)
                self.page.session.set("nickname", response["data"].get("nickname"))
                self.page.session.set("token", response["data"]["token"])
                self.page.session.set("exp", response["data"].get("exp"))
                self.page.session.set(
                    "user_permissions", response["data"]["permissions"]
                )
                self.page.session.set("user_groups", response["data"]["groups"])

                async def refresh_token_periodically():
                    _token_check_logger = logging.getLogger("token_checker")

                    while True:
                        await asyncio.sleep(60)  # 检查间隔（秒）

                        _token_check_logger.info(
                            "Checking if the token needs to be refreshed"
                        )

                        token = self.page.session.get("token")
                        token_exp = self.page.session.get("exp")
                        if not token or not token_exp:
                            _token_check_logger.info(
                                "Doesn't have the conditions to refresh the token, exiting the check"
                            )
                            break

                        if (
                            token_exp and token_exp - time.time() < 300
                        ):  # 5分钟内即将过期
                            _token_check_logger.info("Requesting new token")
                            refresh_resp = build_request(
                                self.page,
                                "refresh_token",
                                username=self.page.session.get("username"),
                                token=token,
                            )
                            if refresh_resp["code"] == 200:
                                self.page.session.set(
                                    "token", refresh_resp["data"]["token"]
                                )
                                self.page.session.set(
                                    "exp", refresh_resp["data"]["exp"]
                                )
                                _token_check_logger.info("Requested new token")
                            else:
                                _token_check_logger.info("Request failed, exiting")
                                break  # 刷新失败，退出线程
                        else:
                            _token_check_logger.info("No need to request a new token")

                self.page.run_task(refresh_token_periodically)

                if {
                    "manage_system",
                    "view_audit_logs",
                    "list_users",
                    "list_groups",
                    "apply_lockdown",
                    "bypass_lockdown",
                } & set(self.page.session.get("user_permissions")):
                    navigation_bar = self.page.session.get("navigation_bar")
                    navigation_bar.destinations.append(
                        ft.NavigationBarDestination(
                            icon=ft.Icons.CLOUD_CIRCLE, label="Manage"
                        )
                    )

                self.login_button.visible = True
                self.loading_animation.visible = False
                self.username_field.value = None
                self.password_field.value = None
                self.username_field.disabled = False
                self.password_field.disabled = False
                self.page.go("/home")

            elif code == 403:
                self.page.session.set("username", self.username_field.value)
                open_change_passwd_dialog(e, "在登录前必须修改密码。")
                self.login_button.visible = True
                self.loading_animation.visible = False
                self.username_field.disabled = False
                self.password_field.disabled = False
                self.update()

            else:
                self.login_button.visible = True
                self.loading_animation.visible = False
                self.username_field.disabled = False
                self.password_field.disabled = False
                self.update()
                self.error_bar.content.value = (
                    f"登录失败：({code}) {response['message']}"
                )
                self.page.open(self.error_bar)

    def sign_up(self, e):
        self.page.go("/signup")
