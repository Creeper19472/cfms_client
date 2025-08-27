# tabs_issue.py
import flet as ft


def main(page: ft.Page):
    page.navigation_bar = ft.NavigationBar(
        destinations=[ft.NavigationBarDestination("111", icon=ft.Icons.ABC)]
    )

    page.add(ft.Card(content=ft.Text("hi")))
    page.add(
        ft.Container(
            content=ft.Tabs(
                tabs=[
                    ft.Tab(
                        "Like", content=ft.Column(controls=[ft.Text("This is a test")])
                    )
                ]
            ),
            margin=10,
            padding=10,
            alignment=ft.alignment.bottom_left, # will cause wrong behavior
            visible=True,
        )
    )


if __name__ == "__main__":
    ft.app(main)
