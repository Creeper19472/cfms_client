from typing import Any, List
import flet as ft


class WelcomeCard(ft.Card):
    def __init__(
        self,
        ref: ft.Ref | None = None,
        width: int | float | None = None,
        height: int | float | None = None,
        left: int | float | None = None,
        top: int | float | None = None,
        right: int | float | None = None,
        bottom: int | float | None = None,
        expand: None | bool | int = None,
        expand_loose: bool | None = None,
        visible: bool | None = None,
        disabled: bool | None = None,
        data: Any = None,
        key: str | None = None,
    ):
        super().__init__(
            ref=ref,
            width=width,
            height=height,
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            expand=expand,
            expand_loose=expand_loose,
            visible=visible,
            disabled=disabled,
            data=data,
            key=key,
        )
        super().__init__()
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ACCESS_TIME_FILLED),
                        title=ft.Text("欢迎访问 保密文档管理系统（CFMS）"),
                        subtitle=ft.Text("落霞与孤鹜齐飞，秋水共长天一色。"),
                    ),
                ]
            ),
            # width=400,
            padding=10,
        )


class HomeTabs(ft.Tabs):
    def __init__(
        self,
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref)
        self.selected_index = 0
        # self.animation_duration = 300
        self.tabs = [
            ft.Tab(
                text="收藏",
                content=ft.Container(
                    ft.Column(
                        controls=[ft.Text("您尚未收藏任何文档或文件夹。")],
                        # alignment=ft.alignment.center,
                    ),
                    margin=15,
                ),
            ),
        ]
        # self.expand = True


class HomeColumn(ft.Column):
    def __init__(self):
        super().__init__()
        self.welcome_card_ref = ft.Ref[ft.Card]()
        self.controls = [
            WelcomeCard(ref=self.welcome_card_ref),
            # ft.Divider(),
            HomeTabs(),
        ]
