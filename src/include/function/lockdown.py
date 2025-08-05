import time
import flet as ft


def go_lockdown(page: ft.Page, timeout: float = 0) -> bool:
    start_time = time.time()
    while not timeout or (time.time() - start_time) <= timeout:
        if page.session.get("initialization_complete"):
            if not page.route.endswith("lockdown"):
                page.go("/lockdown")
            return True
        else:
            time.sleep(0.1)
    return False


def quit_lockdown(page: ft.Page, route="home"):
    if page.route.endswith("lockdown"):
        page.go(route)
