from typing import Optional
import flet as ft


class PathIndicator(ft.Column):
    def __init__(
        self,
        path: Optional[str] = None,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            ref=ref,
        )
        self.text_ref = ft.Ref[ft.Text]()
        self.controls = [ft.Text(ref=self.text_ref)]
        self.text_ref.current.value = path if path else "./"
        self.paths: list[str] = []

    def update_path(self):
        self.text_ref.current.value = "/" + "/".join(self.paths)
        self.update()

    def go(self, path: str):
        self.paths.append(path)
        self.update_path()

    def back(self):
        self.paths.pop()
        self.update_path()
