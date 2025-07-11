# type: ignore
from websockets import ClientConnection
from include.log import getCustomLogger

import flet as ft
from pages.connect import ConnectToServerModel
from pages.home import HomeModel
from pages.login import LoginModel
from pages.manage import ManageModel
from pages.about import AboutModel
from pages.settings import SettingsModel
import threading, sys, platform, os
from flet_permission_handler.permission_handler import (
    PermissionHandler,
    PermissionStatus,
    PermissionType,
)
# import os

# print(os.environ)

def main(page: ft.Page):
    # Page settings
    page.title = "CFMS Client"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1024
    page.window.height = 768
    page.window.resizable = False
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.TRANSPARENT

    page.decoration = ft.BoxDecoration(
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#10162c", "#0c2749", "#0f0f23", "#1a1a2e"],
            tile_mode=ft.GradientTileMode.MIRROR,
        )
    )
    page.theme = ft.Theme(scrollbar_theme=ft.ScrollbarTheme(thickness=0.0))
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.safe_area = True
    page.notch_shape = ft.NotchShape.AUTO

    page.logger = getCustomLogger("client")
    page.session.set("download_lock", threading.Lock())
    page.session.set("upload_lock", threading.Lock())
    page.session.set("communication_lock", threading.Lock())

    page.session.set("version", f"0.0.13.20250712_alpha {page.platform.value}")
    page.session.set("build_version", "v0.0.13")

    page.go("/connect")


if __name__ == "__main__":
    ft.app(target=main)
