import flet as ft
import os

import websockets.exceptions
from include.request import build_request
from include.function.transfer import upload_file_to_server
import requests


__all__ = ["filepicker_ref", "upload_directory"]

filepicker_ref = ft.Ref[ft.FilePicker]()
pick_files_dialog = ft.FilePicker(ref=filepicker_ref, on_result=None)  # init


def upload_directory(event: ft.ControlEvent):

    def select_directory_result(result: ft.FilePickerResultEvent):
        if result.path:

            def build_directory_tree(root_path):
                def build_tree(path):
                    tree = {"files": [], "dirs": {}}
                    for entry in os.scandir(path):
                        if entry.is_dir():
                            tree["dirs"][entry.name] = build_tree(
                                os.path.join(path, entry.name)
                            )
                        elif entry.is_file():
                            tree["files"].append(entry.name)
                    return tree

                return build_tree(root_path)

            root_path = result.path
            tree = build_directory_tree(root_path)

            _alertdialog_ref = ft.Ref[ft.AlertDialog]()
            _ok_ref = ft.Ref[ft.TextButton]()
            _cancel_ref = ft.Ref[ft.TextButton]()

            _progress_column_ref = ft.Ref[ft.Column]()
            _progress_bar_ref = ft.Ref[ft.ProgressBar]()
            _progress_text_ref = ft.Ref[ft.Text]()

            _error_info_ref = ft.Ref[ft.Column]()

            _stop_flag = False

            def _stop_upload(e: ft.ControlEvent):
                nonlocal _stop_flag
                _stop_flag = True

                _cancel_ref.current.disabled = True
                _cancel_ref.current.update()
                return

            # 暂时先采用FTP的模式创建目录树。
            def create_dirs_from_tree(parent_path, tree, parent_id=None):

                # 如果发现终止信号就返回
                if _stop_flag:
                    return

                _progress_text_ref.current.value = f'正在创建目录 "{parent_path}"'
                _progress_bar_ref.current.value = None
                _progress_column_ref.current.update()

                # 在服务器创建目录
                mkdir_resp = build_request(
                    event.page,
                    "create_directory",
                    data={
                        "parent_id": parent_id,
                        "name": os.path.basename(parent_path),
                        "exists_ok": True,
                    },
                    username=event.page.session.get("username"),
                    token=event.page.session.get("token"),
                )

                if mkdir_resp.get("code") != 200:
                    _error_info_ref.current.controls.append(
                        ft.Text(
                            f"Failed to create directory {parent_path}: {mkdir_resp.get('message', 'Unknown error')}"
                        )
                    )
                    _error_info_ref.current.update()
                    return

                # 创建当前目录下的所有子目录
                for dirname, subtree in tree["dirs"].items():
                    dir_path = os.path.join(parent_path, dirname)
                    create_dirs_from_tree(dir_path, subtree, mkdir_resp["data"]["id"])

                # 依次上传文件

                for filename in tree["files"]:

                    # 同样地，如果发现终止信号就返回
                    if _stop_flag:
                        return

                    abs_path = os.path.join(parent_path, filename)

                    _current_number = tree["files"].index(filename) + 1
                    _total_number = len(tree["files"])

                    _progress_text_ref.current.value = (
                        f'[{_current_number}/{_total_number}] 正在上传文件 "{abs_path}"'
                    )
                    _progress_bar_ref.current.value = _current_number / _total_number
                    _progress_column_ref.current.update()

                    create_document_response = build_request(
                        event.page,
                        action="create_document",
                        data={
                            "title": filename,
                            "folder_id": mkdir_resp["data"]["id"],
                            "access_rules": {},
                        },
                        username=event.page.session.get("username"),
                        token=event.page.session.get("token"),
                    )

                    if create_document_response.get("code") != 200:
                        _error_info_ref.current.controls.append(
                            ft.Text(
                                f'创建文件 "{filename}" 失败: {create_document_response.get("message", "Unknown error")}'
                            )
                        )
                        _error_info_ref.current.update()

                    max_retries = 2

                    for retry in range(1, max_retries + 1):
                        try:
                            upload_file_to_server(
                                event.page,
                                create_document_response["data"]["task_data"][
                                    "task_id"
                                ],
                                abs_path,
                                refresh=False,
                            )
                            break
                        except (
                            Exception
                        ) as e:  # (TimeoutError, websockets.exceptions.ConnectionClosedError)
                            if retry >= max_retries:
                                _error_info_ref.current.controls.append(
                                    ft.Text(
                                        f'在上传文件 "{filename}" 时遇到问题：{str(e)}'
                                    )
                                )
                                _error_info_ref.current.update()
                            else:
                                _progress_text_ref.current.value = (
                                    f"正在重试 [{retry}/{max_retries}]: {str(e)}"
                                )
                                _progress_text_ref.current.update()
                            continue

            event.page.add(
                ft.AlertDialog(
                    ref=_alertdialog_ref,
                    title="上传目录",
                    content=ft.Column(
                        [
                            ft.ProgressBar(ref=_progress_bar_ref),
                            ft.Text(
                                ref=_progress_text_ref,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Column(
                                ref=_error_info_ref,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ],
                        ref=_progress_column_ref,
                        width=400,
                        alignment=ft.MainAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    actions=[
                        ft.TextButton(
                            "确定",
                            ref=_ok_ref,
                            on_click=lambda e: e.page.close(_alertdialog_ref.current),
                            disabled=True,
                            # visible=False,
                        ),
                        ft.TextButton("取消", ref=_cancel_ref, on_click=_stop_upload),
                    ],
                    modal=True,
                    scrollable=True,
                )
            )
            event.page.open(_alertdialog_ref.current)

            _progress_text_ref.current.value = "请稍候"
            _progress_column_ref.current.update()

            create_dirs_from_tree(
                root_path, tree, event.page.session.get("current_directory_id")
            )

            load_directory: function = event.page.session.get("load_directory")
            load_directory(event.page, event.page.session.get("current_directory_id"))  # type: ignore

            _ok_ref.current.disabled = False
            _cancel_ref.current.disabled = True
            _alertdialog_ref.current.update()

            if total_errors := len(_error_info_ref.current.controls):
                _progress_text_ref.current.value = (
                    f"上传完成，共计 {total_errors} 个错误。"
                )
                _progress_column_ref.current.update()
            else:
                event.page.close(_alertdialog_ref.current)

            return

    filepicker_ref.current.on_result = select_directory_result
    filepicker_ref.current.get_directory_path()
    event.page.update()
