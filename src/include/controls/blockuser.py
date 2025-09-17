import flet as ft


class UserBlockManager(ft.AlertDialog):
    def __init__(self, username=None):
        super().__init__()
        self.scrollable = True
        self.title = "用户封禁"
        self.content = ft.Column(width=540)

        self.submit_button_ref = ft.Ref[ft.TextButton]()
        self.actions = [
            ft.TextButton("提交", ref=self.submit_button_ref, disabled=True),
            ft.TextButton("取消", on_click=lambda e: e.page.close(self)),
        ]

        if username:
            self.content.controls = [UserBlockModifier(username)]

        # self.content = ft.Column(
        #     [
        #         ft.SearchBar(
        #             visible=bool(username),
        #             view_elevation=4,
        #             divider_color=ft.Colors.AMBER,
        #             bar_hint_text="Search users...",
        #             view_hint_text="Select a user from the suggestions...",
        #             # on_change=handle_change,
        #             # on_submit=handle_submit,
        #             # on_tap=handle_tap,
        #             controls=[
        #                 # ft.ListTile(title=ft.Text(f"Color {i}"), on_click=close_anchor, data=i)
        #                 # for i in range(10)
        #             ],
        #         )
        #     ]
        # )


class UserBlockModifier(ft.Container):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.content = ft.Column(
            [
                ft.Text(f"管理对用户 {self.username} 的封禁"),
                ft.Text("新增封禁", style=ft.TextThemeStyle.TITLE_LARGE),
                # 选择封禁类型
                ft.Text("封禁类型", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.RadioGroup(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Radio(value="all", label="全封禁"),
                                    ft.Text(
                                        "阻止对所有文件和文件夹的新增、编辑、删除和移动，以及阻止其他默认操作",
                                        color=ft.Colors.GREY,
                                    ),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Radio(value="partial", label="部分封禁"),
                                    ft.Text(
                                        "阻止对文件和文件夹的部分操作",
                                        color=ft.Colors.GREY,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    # on_change=radiogroup_changed,
                ),
            ]
        )


def main(page: ft.Page):
    new = UserBlockManager("crp9472")
    page.add(new)
    page.open(new)


if __name__ == "__main__":
    ft.app(main)
