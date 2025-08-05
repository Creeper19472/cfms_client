import ssl, json
import time
from websockets.sync.client import connect
import flet as ft
import threading

from include.function.lockdown import go_lockdown, quit_lockdown


def listen_to_server(page: ft.Page, server_address):

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    websocket = None

    for retry in range(0, max_retries := 5):
        try:
            websocket = connect(
                server_address,
                ssl=ssl_context,
            )
            break
        except TimeoutError:
            continue

    if not websocket:
        return

    register_request = {"action": "register_listener"}

    websocket.send(json.dumps(register_request))
    websocket.recv()

    event_queue: list[tuple[int, dict]] = []

    def handle_events():
        while True:
            for id, event in event_queue:
                if loaded_data["action"] == "lockdown":
                    if not page.session.get("username"):
                        event_queue.append(loaded_data)
                        continue  # 如果尚未登录，则不执行此项
                    if loaded_data["status"]:
                        user_permissions = page.session.get("user_permissions")
                        assert type(user_permissions) == list
                        if "bypass_lockdown" not in user_permissions:
                            go_lockdown(page)
                    else:
                        quit_lockdown(page)
                event_queue.remove((id, event))
            time.sleep(0.1)

    listener_event_handler_thread = threading.Thread(target=handle_events, daemon=True)
    listener_event_handler_thread.start()

    while True:
        raw_data = websocket.recv()
        loaded_data = json.loads(raw_data)
        if not event_queue:
            event_id = 0
        else:
            event_id = event_queue[-1][0] + 1
        event_queue.append((event_id, loaded_data))
