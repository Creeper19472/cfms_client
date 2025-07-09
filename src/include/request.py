import json, time
import ssl
import flet as ft
from websockets.sync.client import connect

def build_request(
    page: ft.Page,
    action: str,
    data: dict = {},
    message: str = "",
    username=None,
    token=None,
    _new_connection=False
) -> dict:
    request = {
        "action": action,
        "data": data,
        "username": username,
        "token": token,
        "timestamp": time.time(),
    }

    request_json = json.dumps(request, ensure_ascii=False)
    
    if _new_connection:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        server_uri = page.session.get("server_uri")
        assert server_uri

        try:
            websocket = connect(server_uri, ssl=ssl_context)
        except:
            raise

    else:
        websocket = page.websocket # type: ignore
        assert websocket
    
    websocket.send(request_json)
    response_json = websocket.recv()

    return json.loads(response_json)
