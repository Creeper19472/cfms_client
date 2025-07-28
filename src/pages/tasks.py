import flet as ft
from flet_model import Model, route
from include.request import build_request
import time
import threading


@route("tasks")
class TasksModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = True
    fullscreen_dialog = True

    tasks_listview = ft.ListView()
    tasks_empty_text = ft.Text("No tasks available", text_align=ft.TextAlign.CENTER, expand=True)
    tasks_empty_info = ft.Column(controls=[tasks_empty_text], expand=True, visible=False)

    controls = [tasks_empty_info, tasks_listview]

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Tasks"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
        )

    def go_back(self, e):
        self.page.views.pop()
        if not self.page.views:
            self.page.go("/home")
        else:
            assert self.page.views[-1].route
            self.page.go(self.page.views[-1].route)

    def post_init(
        self,
    ) -> None:  # 由于每个Model只初始化一次，因此在初始化时先启动定期更新任务状态的线程
        def _action_update_tasks():
            while True:
                self.update_tasks()
                time.sleep(0.5)

        t = threading.Thread(target=_action_update_tasks, daemon=True)
        t.start()

    def update_tasks(self):
        tasks = self.page.session.get("tasks")
        assert type(tasks) is list, "Tasks should be a list"

        updated_tasks = tasks

        for task in tasks:
            assert type(task) is dict, "Each task should be a dictionary"
            if not task.get("id"):
                raise

            for control in self.tasks_listview.controls:
                if getattr(control, "data", None) == task.get("id"):
                    control.data = None # todo
                    # control.

            if task["progress"] >= 100:
                updated_tasks.remove(task)
                continue

        self.page.session.set("tasks", updated_tasks)
        self.tasks_listview.controls.clear()

        for each_task in updated_tasks:
            task_control = ft.ListTile(
                title=ft.Text(each_task["name"]),
                subtitle=ft.Text(f"Progress: {each_task['progress']}%"),
                leading=ft.Icon(ft.Icons.TASK),
                data=each_task["id"],
            )
            self.tasks_listview.controls.append(task_control)

        self.tasks_empty_info.visible = not self.tasks_listview.controls
        self.page.update()
