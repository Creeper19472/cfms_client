import flet as ft
from flet_model import Model, route
from include.request import build_request
from common.notifications import send_error
import requests, os, time

GITHUB_REPO = "Creeper19472/cfms_client"
# GITHUB_REPO = "mihonapp/mihon"
SUPPORTED_PLATFORM = {"windows": "windows", "android": ".apk"}


class GithubAsset:
    def __init__(self, name: str = "", download_link: str = ""):
        self.name = name
        self.download_link = download_link


class GithubRelease:
    def __init__(
        self,
        version: str = "",
        info: str = "",
        release_link: str = "",
        assets: list[GithubAsset] = [],
    ):
        self.version = version  # <- tag_name
        self.info = info  # <- body
        self.release_link = release_link  # <- html_url
        self.assets = assets  # <- assets


def get_latest_release() -> GithubRelease | None:
    # check for updates
    resp = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
    if resp.status_code != 200:
        return

    assets = []
    for asset in resp.json()["assets"]:
        assets.append(
            GithubAsset(
                name=asset["name"],
                download_link=asset["browser_download_url"],
            )
        )

    return GithubRelease(
        version=resp.json()["tag_name"],
        info=resp.json()["body"],
        release_link=resp.json()["html_url"],
        assets=assets,
    )


@route("about")
class AboutModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = True

    appbar = ft.AppBar(
        title=ft.Text("About"),
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.go("/home")
        ),
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
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Copyright © 2025", size=16, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Licensed under Apache License Version 2.0.",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
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
            controls=[], visible=False, scroll=ft.ScrollMode.AUTO
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

            latest = get_latest_release()
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
                ft.Text(
                    latest.info,
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
            ]

            build_version = self.page.session.get("build_version")
            assert build_version

            if not self.is_new_version(False, 0, build_version, latest.version):
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
        if not self.suc_upgrade_button.data:
            return

        self.suc_upgrade_button.disabled = True
        self.page.update()

        upgrade_dialog = ft.AlertDialog(
            modal=True,
            actions=[
                ft.TextButton("取消", on_click=lambda e: e.page.close(upgrade_dialog)),
            ],
        )
        self.page.open(upgrade_dialog)

        self.suc_upgrade_button.disabled = False
        self.page.update()

    def is_new_version(
        self,
        is_preview: bool,
        commit_count: int,
        version_name: str,
        version_tag: str,
    ) -> bool:
        # 移除前缀，如 "r" 或 "v"
        new_version = version_tag[1:]
        if is_preview:
            # 预览版本：基于 "mihonapp/mihon-preview" 仓库的发布
            # 标记为类似 "r1234"
            return new_version.isdigit() and int(new_version) > commit_count
        else:
            # 发布版本：基于 "mihonapp/mihon" 仓库的发布
            # 标记为类似 "v0.1.2"
            old_version = version_name[1:]

            new_sem_ver = [int(part) for part in new_version.split(".")]
            old_sem_ver = [int(part) for part in old_version.split(".")]

            for index, (new_part, old_part) in enumerate(zip(new_sem_ver, old_sem_ver)):
                if new_part > old_part:
                    return True

            return False

    def post_init(self) -> None:
        self.check_for_updates()


# class GetApplicationRelease(
#     service: ReleaseService,
#     preference_store: PreferenceStore,
# ):
#     def __init__(self):
#         self.last_checked = self.preference_store.get_long(
#             preference_store.app_state_key("last_app_check"), 0
#         )

#     async def await(self, arguments: Arguments) -> Result:
#         now = datetime.datetime.now()

#         # 限制检查频率，最多每3天检查一次
#         next_check_time = datetime.datetime.fromtimestamp(
#             self.last_checked.get()
#         ) + datetime.timedelta(days=3)
#         if not arguments.force_check and now < next_check_time:
#             return Result.NoNewUpdate

#         release = await service.latest(arguments)  # 使用 await 因为 service.latest 是异步的
#         if release is None:
#             return Result.NoNewUpdate

#         self.last_checked.set(now.timestamp())

#         # 检查最新版本是否与当前版本不同
#         is_new_version = self.is_new_version(
#             arguments.is_preview,
#             arguments.commit_count,
#             arguments.version_name,
#             release.version,
#         )
#         return Result.NewUpdate(release) if is_new_version else Result.NoNewUpdate


#     class Arguments:
#         def __init__(self, is_foss: bool, is_preview: bool, commit_count: int, version_name: str, repository: str, force_check: bool = False):
#             self.is_foss = is_foss
#             self.is_preview = is_preview
#             self.commit_count = commit_count
#             self.version_name = version_name
#             self.repository = repository
#             self.force_check = force_check

#     class Result:
#         class NewUpdate:
#             def __init__(self, release: Release):
#                 self.release = release

#         class NoNewUpdate:
#             pass

#         class OsTooOld:
