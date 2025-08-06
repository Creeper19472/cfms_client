import asyncio
import flet as ft


class EmergencyInfoBar(ft.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._progress_bar_ref = ft.Ref[ft.ProgressBar]()
        self.controls = [
            ft.ProgressBar(color=ft.Colors.RED, ref=self._progress_bar_ref),
            ft.Text("紧急状态"),
        ]
        self.horizontal_alignment=ft.CrossAxisAlignment.CENTER
        self.visible=True

    # def did_mount(self):
    #     self.running = True

    #     assert self.page
    #     self.page.run_task(self.update_bar)

    # def will_unmount(self):
    #     self.running = False
    
    # async def update_bar(self):
    #     while self.running:
    #         self._progress_bar_ref.current.value = 0 if self._progress_bar_ref.current.value else 1
    #         self.update()
    #         await asyncio.sleep(1)
    