# type: ignore
from websockets import ClientConnection
from include.log import getCustomLogger
import asyncio

import flet as ft
from pages.connect import ConnectToServerModel
from pages.home import HomeModel
from pages.login import LoginModel
from pages.manage import ManageModel
from pages.about import AboutModel
from pages.settings import SettingsModel
from pages.tasks import TasksModel
from pages.lockdown import LockdownModel
from pages.interface.move import MoveObjectModel
import threading, sys, platform, os
from flet_permission_handler.permission_handler import (
    PermissionHandler,
    PermissionStatus,
    PermissionType,
)
from include.constants import FLET_APP_STORAGE_TEMP

from include.controls.emergency import EmergencyInfoBar

import logging
logging.basicConfig(level=logging.INFO)

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

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "S" and e.ctrl:
            page.show_semantics_debugger = not page.show_semantics_debugger
            page.update()

    page.on_keyboard_event = on_keyboard

    def event(e: ft.AppLifecycleStateChangeEvent):
        if e.data=='detach' and page.platform == ft.PagePlatform.ANDROID:
            os._exit(1)

    page.on_app_lifecycle_state_change = event

    page.decoration = ft.BoxDecoration(
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#10162c", "#0c2749", "#0f0f23", "#1a1a2e"],
            tile_mode=ft.GradientTileMode.MIRROR,
        )
    )

    page.fonts = {
        "Source Han Serif SC Regular": "/fonts/SourceHanSerifSC/SourceHanSerifSC-Regular.otf",
        # "Deng": "/fonts/Deng.ttf",
        # "Deng Bold": "/fonts/Dengb.ttf",
        # "Deng Light": "/fonts/Dengl.ttf"
    }

    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(thickness=0.0),
        # dialog_theme=ft.DialogTheme(title_text_style=ft.TextStyle(size=22, font_family="Deng Bold")),
        # text_button_theme=ft.TextButtonTheme(text_style=ft.TextStyle(font_family="Deng")),
        # elevated_button_theme=ft.ElevatedButtonTheme(text_style=ft.TextStyle(font_family="Deng")),
        font_family="Source Han Serif SC Regular",
    )
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.safe_area = True
    page.notch_shape = ft.NotchShape.AUTO

    page.logger = getCustomLogger("client")
    page.session.set("download_lock", threading.Lock())
    page.session.set("upload_lock", threading.Lock())
    # page.session.set("communication_lock", threading.Lock())

    page.session.set("tasks", [])

    page.session.set("version", f"0.1.8.20250816_alpha {page.platform.value}")
    page.session.set("build_version", "v0.1.8")
    page.session.set("protocol_version", 3)

    emergency_info_ref = ft.Ref[ft.Column]()

    async def check_emergency():
        while True:
            emergency_info_ref.current.visible = bool(page.session.get("lockdown"))
            emergency_info_ref.current.update()
            await asyncio.sleep(1)

    page.overlay.append(EmergencyInfoBar(ref=emergency_info_ref, visible=False))
    page.update()
    page.run_task(check_emergency)

    import glob

    # 删除所有旧安装包
    for file in glob.glob(f"{FLET_APP_STORAGE_TEMP}/*.zip"):
        os.remove(file)

    for file in glob.glob(f"{FLET_APP_STORAGE_TEMP}/*.apk"):
        os.remove(file)

    for file in glob.glob(f"{FLET_APP_STORAGE_TEMP}/*.sha1"):
        os.remove(file)

    for file in glob.glob(f"{FLET_APP_STORAGE_TEMP}/*.checksum"):
        os.remove(file)

    page.go("/connect")


if __name__ == "__main__":
    ft.app(target=main)
