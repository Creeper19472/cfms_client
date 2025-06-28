import flet as ft
from flet_model import Model, route


class ManagementNavBar(ft.NavigationBar):
    def __init__(self):
        nav_destinations = [
            ft.NavigationBarDestination(
                icon=ft.Icons.SUPERVISOR_ACCOUNT_OUTLINED, label="Accounts"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
                label="User Groups & Permissions",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_APPLICATIONS, label="Settings"
            ),
        ]

        super().__init__(
            nav_destinations,
            selected_index=0,
            on_change=self.on_change_item,
            # visible=False
        )

    def on_change_item(self, e: ft.ControlEvent):
        control: ManagementNavBar = e.control
        match control.selected_index:
            case 0:  # Manage Accounts
                manage_accounts_container.visible = True
                e.page.update()
            #     home_container.visible = False
            #     load_directory(self.page, folder_id=current_directory_id)

            # case 1:
            #     manage_accounts_container.visible = False
            #     home_container.visible = True
            #     self.page.update()
            # case 2:
            #     manage_accounts_container.visible = False
            #     home_container.visible = False
            #     self.page.update()


manage_accounts_container = ft.Container(
    content=ft.Column(
        controls=[
            ft.DataTable(
                columns=[
                    ft.DataColumn(label=ft.Text("User ID")),
                    ft.DataColumn(label=ft.Text("Username")),
                    ft.DataColumn(label=ft.Text("Email")),
                    ft.DataColumn(label=ft.Text("Role")),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("001")),
                            ft.DataCell(ft.Text("john_doe")),
                            ft.DataCell(ft.Text("john.doe@example.com")),
                            ft.DataCell(ft.Text("Admin")),
                        ]
                    ),
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("002")),
                            ft.DataCell(ft.Text("jane_smith")),
                            ft.DataCell(ft.Text("jane.smith@example.com")),
                            ft.DataCell(ft.Text("User")),
                        ]
                    ),
                    # Add more rows as needed
                ],
                column_spacing=10,
            )
        ]
    ),
    margin=10,
    padding=10,
    alignment=ft.alignment.top_center,
    visible=True,
    expand=True,
    expand_loose=True
)


@route("manage")
class ManageModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    appbar = ft.AppBar(
        title=ft.Text("Management"),
        center_title=True,
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.go("/home")
        ),
    )
    navigation_bar = ManagementNavBar()

    controls = [manage_accounts_container]
