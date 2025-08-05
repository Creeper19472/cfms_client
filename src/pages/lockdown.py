import flet as ft
from flet_model import Model, route
from include.function.lockdown import go_lockdown, quit_lockdown
from include.request import build_request
import time
import threading


@route("lockdown")
class LockdownModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    form_container_ref = ft.Ref[ft.Container]()
    time_ref = ft.Ref[ft.Text]()

    # appbar = ft.AppBar(title=ft.Text("Connect to Server"), center_title=True)

    def connect_button_clicked(self, e):
        pass

    def __init__(self, page: ft.Page):
        super().__init__(page)

        container = ft.Container(
            ref=self.form_container_ref,
            # width=FORM_WIDTH,
            # bgcolor=FIELD_BG,
            # border_radius=BUTTON_RADIUS,
            padding=20,
            content=ft.Column(
                controls=[
                    # self.input_text_field,
                    ft.Column(
                        controls=[
                            ft.Text(
                                value="紧急状态已启用",
                                size=32,
                                # text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                value="一名管理员已在服务器全局启用紧急状态模式。在该状态结束前，您将不能正常进行任何操作。",
                                # text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                value="如有疑问，请询问系统管理员。",
                            ),
                            ft.Text(
                                value="启用紧急状态的原因：（无）",
                            ),
                            ft.Container(content=ft.Text(value=None, ref=self.time_ref), padding=25)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        expand=True
                    ),
                ],
                spacing=15,
            ),
        )

        self.controls = [container]

    def post_init(self) -> None:
        def _update_time():
            while True:
                # 因为没有找到再次初始化 Model 的好方法，所以不能贸然终止这个线程.
                if self.page.route.endswith("lockdown"): 
                    self.time_ref.current.value = time.asctime()
                    self.time_ref.current.update()
                time.sleep(0.5)

        new_thread = threading.Thread(target=_update_time, daemon=True)
        new_thread.start()

