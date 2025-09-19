from typing import Optional
import flet as ft
import json
from include.request import build_request
from common.notifications import send_error


class RequestDialog(ft.AlertDialog):
    def __init__(
        self,
        path: Optional[str] = None,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            ref=ref,
        )
        self.req_name_ref = ft.Ref[ft.TextField]()
        self.req_data_ref = ft.Ref[ft.TextField]()
        self.result_ref = ft.Ref[ft.TextField]()
        self.content = ft.Column(
            [
                ft.TextField(label="Request Name", ref=self.req_name_ref),
                ft.TextField(label="Request Data", ref=self.req_data_ref),
                ft.TextField(label="Result", ref=self.result_ref, read_only=True, multiline=True, min_lines=5)
            ],
            width=720
        )
        self.actions = [
            ft.TextButton("Submit", on_click=self.on_submit_button_clicked),
            ft.TextButton("Cancel", on_click=lambda e: e.page.close(self)),
        ]
        self.scrollable = True

    def on_submit_button_clicked(self, event: ft.ControlEvent):
        assert self.page
        request_name: str | None = self.req_name_ref.current.value
        text_data: str | None = self.req_data_ref.current.value

        if not request_name:
            send_error(self.page, "Request name must be specified")
            return

        if text_data:
            try:
                data_to_send = json.loads(text_data)
            except json.JSONDecodeError as e:
                send_error(self.page, str(e))
                return
        else:
            data_to_send = {}

        resp = build_request(
            self.page,
            request_name,
            data_to_send,
            username=self.page.session.get("username"),
            token=self.page.session.get("token"),
        )
        self.result_ref.current.value = json.dumps(resp)
        self.update()
