import json, time
import flet as ft


def build_request(
    page: ft.Page,
    action: str,
    data: dict = {},
    message: str = "",
    username=None,
    token=None,
) -> dict:
    request = {
        "action": action,
        "data": data,
        "username": username,
        "token": token,
        "timestamp": time.time(),
    }

    request_json = json.dumps(request, ensure_ascii=False)
    page.websocket.send(request_json)  # type: ignore
    response_json = page.websocket.recv()  # type: ignore

    return json.loads(response_json)
