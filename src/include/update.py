import requests
import os
from include.constants import RUNTIME_PATH, FLET_APP_STORAGE_TEMP


GITHUB_REPO = "Creeper19472/cfms_client_next"
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
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        )
        if resp.status_code != 200:
            return
    except requests.exceptions.ConnectionError:
        raise  # leave it to the parent to handle

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


def is_new_version(
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
