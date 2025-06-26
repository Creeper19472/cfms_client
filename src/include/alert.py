import flet as ft

TEXT_COLOR = "#f3f4f6"  # Near-white for clarity
ERROR_COLOR = "#f87171"  # Softer red for errors

def send_error(page: ft.Page, message: str):
    error_snack_bar = ft.SnackBar(
        content=ft.Text(message),
        show_close_icon=True,
        duration=4.0, # type: ignore
        behavior=ft.SnackBarBehavior.FLOATING,
        bgcolor=ERROR_COLOR,
    )
    page.overlay.append(error_snack_bar)
    error_snack_bar.open = True
    page.update()