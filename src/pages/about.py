import flet as ft
from flet_open_file import FletOpenFile
from flet_model import Model, route
from include.request import build_request
from include.update import SUPPORTED_PLATFORM, get_latest_release, is_new_version
from include.constants import RUNTIME_PATH, FLET_APP_STORAGE_TEMP
from common.notifications import send_error
import requests, os, time
import threading
from flet_permission_handler import PermissionHandler, PermissionType, PermissionStatus


SUPPORTED_PLATFORM: dict
RUNTIME_PATH: str
FLET_APP_STORAGE_TEMP: str


@route("about")
class AboutModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = True

    _appbar_ref = ft.Ref[ft.AppBar]()
    _leading_ref = ft.Ref[ft.IconButton]()

    appbar = ft.AppBar(
        title=ft.Text("About"),
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: e.page.go("/home"),
            ref=_leading_ref,
        ),
        ref=_appbar_ref,
    )

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.about_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Classified File Management System Client",
                        size=22,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"Version: {page.session.get("version")}",
                        size=16,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        "Copyright © 2025 Creeper Team",
                        size=16,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        "Licensed under Apache License Version 2.0.",
                        size=16,
                        text_align=ft.TextAlign.LEFT,
                    ),
                ],
                expand=True,
            ),
            margin=10,
            padding=10,
            # alignment=ft.alignment.center,
            visible=True,
        )

        self.suc_update_button = ft.IconButton(
            icon=ft.Icons.UPDATE,
            on_click=lambda e: self.check_for_updates(),
        )
        self.suc_progress_ring = ft.ProgressRing(visible=False)
        self.suc_progress_text = ft.Text("正在检查更新", visible=False)
        self.suc_environ_unavailable_text = ft.Text(
            "无法更新：源代码运行时不能检查更新。", visible=False
        )
        self.suc_unavailable_text = ft.Text(visible=False)

        self.suc_upgrade_button = ft.ElevatedButton(
            "更新",
            on_click=lambda e: self.do_release_upgrade(),
            visible=False,
        )
        self.suc_release_info = ft.Column(
            controls=[], visible=False, scroll=ft.ScrollMode.AUTO, expand=True
        )

        self.software_updater_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "软件更新",
                                size=22,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            self.suc_update_button,
                            self.suc_upgrade_button,
                        ]
                    ),
                    ft.Column(
                        controls=[
                            self.suc_progress_ring,
                            self.suc_progress_text,
                            self.suc_unavailable_text,
                            self.suc_environ_unavailable_text,
                            self.suc_release_info,
                        ],
                    ),
                ],
            ),
            margin=10,
            padding=10,
            # alignment=ft.alignment.center,
            visible=True,
        )

        self.controls = [self.about_container, self.software_updater_container]

    def check_for_updates(self):
        self.suc_update_button.disabled = True

        self.suc_upgrade_button.visible = False
        self.suc_upgrade_button.disabled = False

        self.suc_progress_ring.visible = True
        self.suc_progress_text.visible = True
        self.suc_environ_unavailable_text.visible = False
        self.suc_unavailable_text.visible = False
        self.suc_release_info.visible = False
        self.page.update()

        def _impl_check_for_updates():

            # 设定运行架构下要查找的版本。
            match_text = SUPPORTED_PLATFORM.get(self.page.platform.value)

            try:
                latest = get_latest_release()
            except requests.exceptions.ConnectionError as e:
                send_error(self.page, f"连接失败：{e.strerror}")
                return

            if not latest:
                self.suc_unavailable_text.value = "未获取到版本信息"
                self.suc_unavailable_text.visible = True
                return

            self.suc_release_info.controls = [
                ft.Text(
                    f"当前版本：{self.page.session.get('version')}",
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Text(
                    f"最新版本：{latest.version}",
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Text(
                    "更新说明：",
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Markdown(
                    latest.info,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    on_tap_link=lambda e: e.page.launch_url(e.data),
                ),
            ]

            build_version = self.page.session.get("build_version")
            assert build_version

            if not is_new_version(False, 0, build_version, latest.version):
                self.suc_unavailable_text.value = "已是最新版本"
                self.suc_unavailable_text.visible = True
                return

            if match_text:
                for asset in latest.assets:
                    if match_text in asset.name:
                        self.suc_upgrade_button.data = (
                            asset.download_link
                        )  # 设置下载链接
                        self.suc_upgrade_button.visible = True
                        self.suc_release_info.visible = True
                        break  # releases 方面应当保证匹配结果唯一，如果唯一的话就没必要继续匹配了

                # 判断是否有找到对应架构的包
                if not self.suc_upgrade_button.visible:
                    self.suc_unavailable_text.value = "未在最新版本中找到对应架构的包"
                    self.suc_unavailable_text.visible = True
            else:
                self.suc_unavailable_text.value = "没有找到更新：不支持的架构"
                self.suc_unavailable_text.visible = True

        if os.environ.get("FLET_APP_CONSOLE"):
            _impl_check_for_updates()
        else:
            time.sleep(1)
            self.suc_environ_unavailable_text.visible = True

        self.suc_update_button.disabled = False
        self.suc_progress_ring.visible = False
        self.suc_progress_text.visible = False
        self.page.update()

    def do_release_upgrade(self):
        if not (download_url := self.suc_upgrade_button.data):
            return
        assert type(download_url) == str
        save_filename = download_url.split("/")[-1]

        self.suc_upgrade_button.disabled = True
        self.page.update()

        def _stop_upgrade(e: ft.ControlEvent):
            download_thread.stop()
            e.page.close(upgrade_dialog)

        upgrade_special_button = FletOpenFile(
            value=None, text="执行更新", visible=True  # False
        )
        upgrade_special_note = ft.Text(
            "您使用的设备需要手动执行更新。再次点击“执行更新”以继续。", visible=False
        )
        upgrade_note = ft.Text(visible=False)
        upgrade_progress = ft.ProgressRing(visible=False)
        upgrade_progress = ft.ProgressBar()
        upgrade_progress_text = ft.Text(value="正在准备下载")
        upgrade_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("更新"),
            content=ft.Column(
                controls=[
                    upgrade_progress,
                    upgrade_progress_text,
                    upgrade_note,
                    upgrade_special_note,
                ],
                # spacing=15,
                width=400,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            actions=[
                # upgrade_special_button,
                ft.TextButton("取消", on_click=_stop_upgrade),
            ],
            # scrollable=True,
        )
        self.page.open(upgrade_dialog)

        class UpdateDownloadThread(threading.Thread):
            def __init__(self, download_url: str, save_filename: str, page: ft.Page):
                super().__init__()
                self.download_url = download_url
                self.save_filename = save_filename
                self.page = page
                self._stop_event = threading.Event()

            def run(self):
                if self._download_update():
                    # print(os.getcwd())
                    if self.page.platform.value == "windows":
                        # os.startfile(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                        # 开始执行安装
                        upgrade_progress_text.visible = False
                        upgrade_note.value = "正在解压缩版本包"
                        upgrade_note.visible = True
                        self.page.update()

                        from zipfile import ZipFile
                        import subprocess

                        with ZipFile(
                            f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "r"
                        ) as zip_ref:
                            zip_ref.extractall(f"{FLET_APP_STORAGE_TEMP}/update")

                        upgrade_note.value = "正在删除已解压缩的包"
                        self.page.update()

                        try:
                            os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                        except FileNotFoundError:
                            pass
                        except Exception as e:
                            send_error(self.page, f"删除临时文件失败：{e}")

                        upgrade_note.value = "正在写入更新脚本"
                        self.page.update()

                        _update_script = f'taskkill -f -im cfms_client.exe & xcopy "{FLET_APP_STORAGE_TEMP}/update/build/windows" "{RUNTIME_PATH}" /I /Y /S & rmdir /s /q "{FLET_APP_STORAGE_TEMP}/update"'
                        with open(f"{FLET_APP_STORAGE_TEMP}/update.cmd", "w") as f:
                            f.write(_update_script)

                        upgrade_note.value = "正在关闭应用"
                        self.page.update()

                        # os.system(f'start "{FLET_APP_STORAGE_TEMP}/update.cmd"')
                        subprocess.run(
                            ["cmd", "/c", f"{FLET_APP_STORAGE_TEMP}/update.cmd"]
                        )
                        self.page.window.close()

                    else:
                        upgrade_special_button.value = (
                            f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}"
                        )
                        # print(upgrade_special_button.value)

                        self.ph = self.page.session.get("ph")
                        assert type(self.ph) == PermissionHandler
                        if (
                            self.ph.request_permission(
                                PermissionType.REQUEST_INSTALL_PACKAGES
                            )
                            == PermissionStatus.DENIED
                        ):
                            send_error(
                                self.page,
                                "授权失败，您将无法正常安装更新。请在设置中允许应用安装更新。",
                            )

                        # upgrade_special_button.visible = True
                        upgrade_special_note.visible = True
                        upgrade_dialog.actions.insert(0, upgrade_special_button)
                        self.page.update()
                        # upgrade_special_button.update()

            def stop(self):
                self._stop_event.set()

            def _download_update(self):
                try:
                    response = requests.get(self.download_url, stream=True)
                    if response.status_code == 200:
                        total_size = response.headers["content-length"]
                        # print(response.headers)
                        with open(
                            f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "wb"
                        ) as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if self._stop_event.is_set():
                                    break
                                if chunk:
                                    f.write(chunk)
                                    upgrade_progress.value = (
                                        int(f.tell() * 100 / int(total_size)) / 100
                                    )
                                    upgrade_progress_text.value = f"{int(f.tell() * 100 / int(total_size))}% ({int(f.tell())} / {total_size})"
                                    self.page.update()
                        if self._stop_event.is_set():
                            try:
                                os.remove(
                                    f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}"
                                )
                            except FileNotFoundError:
                                pass
                            return False
                        else:
                            return True

                    return False

                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.SSLError,
                ) as e:
                    send_error(self.page, f"在更新时发生错误：{e.strerror}")
                    return False

        # Start the download in a separate thread
        download_thread = UpdateDownloadThread(download_url, save_filename, self.page)
        download_thread.start()
        download_thread.join()

        self.suc_upgrade_button.disabled = False
        self.page.update()

    def _go_back(self, event: ft.ControlEvent):
        self.page.views.pop()
        if last_route := self.page.views[-1].route:
            self.page.go(last_route)

    def post_init(self) -> None:
        self._leading_ref.current.on_click = self._go_back
        self._leading_ref.current.update()
        self.check_for_updates()
