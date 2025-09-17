import flet as ft


def main(page: ft.Page):
    page.navigation_bar = ft.NavigationBar(
        destinations=[ft.NavigationBarDestination(icon=ft.Icons.ABC, label="One")]
    )

    page.add(ft.Card(content=ft.Text("My card")))
    page.add(
        ft.Container(
            margin=10,
            padding=10,
            alignment=ft.Alignment.TOP_CENTER,
            expand=True,
            content=ft.Tabs(
                length=2,
                content=ft.Column(
                    controls=[
                        ft.TabBar(tabs=[ft.Tab(label="One"), ft.Tab(label="Two")]),
                        ft.TabBarView(
                            expand=True,
                            controls=[ft.Text("Content 1"), ft.Text("Content 2")],
                        ),
                    ],
                ),
            ),
        )
    )


ft.run(main)