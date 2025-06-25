# type: ignore

from typing import TYPE_CHECKING
import flet as ft
import logging

LOGGER = logging.getLogger(__name__)

class MyNavBar(ft.NavigationBar):
    def __init__(self):
        super().__init__(
            [
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER, label="Files"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ],
            selected_index=1,
            on_change=self.on_change_item,
            # visible=False
        )
    
    def on_change_item(self, e):
        match e.control.selected_index:
            case 0:
                self.page.go("/files")
            case 1:
                self.page.go("/home")
            case 2:
                self.page.go("/settings")
            # case 3:
            #     self.page.go("/rounds")
            # case 4:
            #     self.page.go("/logos")
            # case 5:
            #     self.page.go("/slides")