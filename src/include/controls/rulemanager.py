import asyncio
import json
from typing import Any, Callable, List
from include.request import build_request
from common.notifications import send_error
import flet as ft


class RuleManager(ft.AlertDialog):
    def __init__(
        self,
        object_id: str,
        object_type: str,
        modal: bool = False,
        title: ft.Control | str | None = None,
        content: ft.Control | None = None,
        actions: List[ft.Control] | None = None,
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None,
        elevation: int | float | None = None,
        icon: ft.Control | None = None,
        open: bool = False,
        title_padding: int | float | ft.Padding | None = None,
        content_padding: int | float | ft.Padding | None = None,
        actions_padding: int | float | ft.Padding | None = None,
        actions_alignment: ft.MainAxisAlignment | None = None,
        shape: ft.OutlinedBorder | None = None,
        inset_padding: int | float | ft.Padding | None = None,
        icon_padding: int | float | ft.Padding | None = None,
        action_button_padding: int | float | ft.Padding | None = None,
        surface_tint_color: str | ft.Colors | ft.CupertinoColors | None = None,
        shadow_color: str | ft.Colors | ft.CupertinoColors | None = None,
        icon_color: str | ft.Colors | ft.CupertinoColors | None = None,
        scrollable: bool | None = None,
        actions_overflow_button_spacing: int | float | None = None,
        alignment: ft.Alignment | None = None,
        content_text_style: ft.TextStyle | None = None,
        title_text_style: ft.TextStyle | None = None,
        clip_behavior: ft.ClipBehavior | None = None,
        semantics_label: str | None = None,
        barrier_color: str | ft.Colors | ft.CupertinoColors | None = None,
        on_dismiss: Callable[[ft.ControlEvent], Any] | None = None,
        ref: ft.Ref | None = None,
        disabled: bool | None = None,
        visible: bool | None = None,
        data: Any = None,
        adaptive: bool | None = None,
    ):
        super().__init__(
            modal,
            title,
            content,
            actions,
            bgcolor,
            elevation,
            icon,
            open,
            title_padding,
            content_padding,
            actions_padding,
            actions_alignment,
            shape,
            inset_padding,
            icon_padding,
            action_button_padding,
            surface_tint_color,
            shadow_color,
            icon_color,
            scrollable,
            actions_overflow_button_spacing,
            alignment,
            content_text_style,
            title_text_style,
            clip_behavior,
            semantics_label,
            barrier_color,
            on_dismiss,
            ref,
            disabled,
            visible,
            data,
            adaptive,
        )
        self.content_ref = ft.Ref[ft.TextField]()
        self.submit_button_ref = ft.Ref[ft.TextButton]()
        self.action_progress_ring_ref = ft.Ref[ft.ProgressRing]()

        self.title = "规则管理器"
        self.content = ft.Column(
            controls=[
                ft.TextField(
                    label="规则内容",
                    multiline=True,
                    min_lines=5,
                    ref=self.content_ref,
                    # max_lines=3,
                ),
                ft.Markdown(
                    "有关规则格式的说明，请参见 [CFMS 服务端文档](https://cfms-server-doc.readthedocs.io/zh-cn/latest/groups_and_rights.html#match-rules)。",
                    selectable=False,
                    on_tap_link=lambda e: self.on_link_tapped(e.data),
                ),
            ],
            expand=True,
            width=720,
        )
        self.actions = [
            ft.ProgressRing(ref=self.action_progress_ring_ref, visible=False),
            ft.TextButton(
                "提交", ref=self.submit_button_ref, on_click=self.submit_rule
            ),
            ft.TextButton("取消", on_click=lambda event: self.close()),
        ]

        self.scrollable = True

        self.object_id = object_id
        self.object_type = object_type

    def close(self):
        assert self.page
        self.page.close(self)

    def on_link_tapped(self, url):
        assert self.page
        self.page.launch_url(url)

    def did_mount(self):
        assert self.page
        self.page.run_task(self.update_rule)

    def will_unmount(self): ...

    def lock_edit(self):
        assert self.page
        self.content_ref.current.disabled = True
        self.action_progress_ring_ref.current.visible = True
        self.submit_button_ref.current.visible = False  # will work in flet v1
        self.page.update()

    def unlock_edit(self):
        assert self.page
        self.content_ref.current.disabled = False
        self.action_progress_ring_ref.current.visible = False
        self.submit_button_ref.current.visible = True  # will work in flet v1
        self.page.update()

    async def update_rule(self):
        match self.object_type:
            case "document":
                action = "get_document_access_rules"
                data = {"document_id": self.object_id}
            # case "directory":
            #     action = "get_directory_info"
            #     data = {"directory_id": self.object_id}
            case _:
                raise ValueError(f"Invaild object type '{self.object_type}'")
        assert self.page

        self.lock_edit()

        info_resp = build_request(
            self.page,
            action,
            data,
            username=self.page.session.get("username"),
            token=self.page.session.get("token"),
        )
        if info_resp["code"] != 200:
            self.content_ref.current.value = (
                f"Failed to fetch current rules: {info_resp['message']}"
            )
        else:
            access_rules = info_resp["data"]
            self.content_ref.current.value = json.dumps(access_rules)
            self.unlock_edit()
        self.content_ref.current.update()

    def submit_rule(self, event: ft.ControlEvent):
        assert self.page
        self.lock_edit()

        match self.object_type:
            case "document":
                action = "set_document_rules"
                try:
                    data = {
                        "document_id": self.object_id,
                        "access_rules": (
                            json.loads(self.content_ref.current.value)
                            if self.content_ref.current.value
                            else {}
                        ),
                    }
                except json.decoder.JSONDecodeError:
                    send_error(self.page, "提交的规则不是有效的JSON")
                    self.close()
                    return

            case "directory":
                action = "set_directory_rules"
                data = {"directory_id": self.object_id}
            case _:
                raise ValueError(f"Invaild object type '{self.object_type}'")

        submit_resp = build_request(
            self.page,
            action,
            data,
            username=self.page.session.get("username"),
            token=self.page.session.get("token"),
        )

        if submit_resp["code"] != 200:
            send_error(self.page, f"修改失败：{submit_resp["message"]}")

        self.close()
