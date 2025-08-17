# type: ignore
import flet as ft
import json
import base64, time
import os, sys
import shutil

# from Crypto.Cipher import AES
from include.log import getCustomLogger
from common.notifications import send_error
import mmap, hashlib, ssl
from websockets.sync.client import connect
import websockets.exceptions
import threading
import traceback
from include.constants import FLET_APP_STORAGE_TEMP
from Crypto.Cipher import AES


def calculate_sha256(file_path):
    # 使用更快的 hashlib 工具和内存映射文件
    with open(file_path, "rb") as f:
        # 使用内存映射文件直接映射到内存
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()


def receive_file_from_server(page: ft.Page, task_id: str, filename: str = None) -> None:
    """
    Receives a file from the server over a websocket connection using AES encryption.
    The method performs the following steps:
    1. Receives the file metadata including the SHA-256 hash and file size.
    2. Acknowledges readiness to receive the file.
    3. Receives the file in encrypted chunks, decrypts each chunk using AES-256 in CFB mode.
    4. Writes the decrypted data to a local file.
    5. Verifies the received file's SHA-256 hash and size.
    6. Handles errors and logs relevant information.
    Args:
        task_id (str): The identifier for the task whose associated file is to be received.
    Raises:
        ValueError: If the file metadata or transfer cannot be processed correctly.
        Exception: If an error occurs during file decryption or saving.
    Returns:
        None
    """

    download_lock: threading.Lock = page.session.get("download_lock")
    if not download_lock.acquire(timeout=0):
        send_error(page, "不能同时下载多个文件")
        return

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        websocket = connect(
            page.session.get("server_uri"), ssl=ssl_context, max_size=1024**2 * 4
        )
    except Exception as e:
        download_lock.release()
        raise NotImplementedError

    # Send the request for file metadata
    websocket.send(
        json.dumps(
            {
                "action": "download_file",
                "data": {"task_id": task_id},
            },
            ensure_ascii=False,
        )
    )

    # Receive file metadata from the server
    response = json.loads(websocket.recv())
    if response["action"] != "transfer_file":
        page.logger.error("Invalid action received for file transfer.")
        return

    sha256 = response["data"].get("sha256")  # 原始文件的 SHA256
    file_size = response["data"].get("file_size")  # 原始文件的大小
    chunk_size = response["data"].get("chunk_size", 8192)  # 分片大小
    total_chunks = response["data"].get("total_chunks")  # 分片总数

    websocket.send("ready")

    downloading_path = FLET_APP_STORAGE_TEMP + "/downloading/" + task_id
    os.makedirs(downloading_path, exist_ok=True)

    if page.platform.value in ["android"]:
        file_path = f"/storage/emulated/0/{filename if filename else sha256[0:17]}"
    else:
        file_path = f"./{filename if filename else sha256[0:17]}"

    if not file_size:
        with open(file_path, "wb") as f:
            f.truncate(0)
        download_lock.release()
        page.logger.info(f"Empty file, skipping")
        return

    try:
        progress_bar = ft.ProgressBar()
        progress_info = ft.Text(text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE)
        progress_column = ft.Column(
            controls=[progress_bar, progress_info],
            alignment=(
                ft.MainAxisAlignment.START
                if os.name == "nt"
                else ft.MainAxisAlignment.END
            ),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        page.overlay.append(progress_column)
        # page.overlay.append(progress_bar)
        page.update()

        try:

            received_chunks = 0
            iv: bytes = b""

            while received_chunks + 1 <= total_chunks:
                # Receive encrypted data from the server
                # data = websocket.recv()
                # f.write(data)
                # progress_bar.value = f.tell() / file_size
                # progress_info.value = (
                #     f"{f.tell() / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                # )
                # page.update()

                data = websocket.recv()
                if not data:
                    raise ValueError("Received empty data from server")
                    # break

                data_json: dict = json.loads(data)
                # print(data_json)

                index = data_json["data"].get("index")
                if index == 0:
                    iv = base64.b64decode(data_json["data"].get("iv"))
                chunk_hash = data_json["data"].get("hash")  # provided but unused
                chunk_data = base64.b64decode(data_json["data"].get("chunk"))
                chunk_file_path = os.path.join(downloading_path, str(index))

                with open(chunk_file_path, "wb") as chunk_file:
                    chunk_file.write(chunk_data)

                received_chunks += 1

                if received_chunks < total_chunks:
                    received_file_size = chunk_size * received_chunks
                else:
                    received_file_size = file_size

                progress_bar.value = received_file_size / file_size
                progress_info.value = f"{received_file_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                page.update()

            # 获得解密信息
            decrypted_data = websocket.recv()
            decrypted_data_json: dict = json.loads(decrypted_data)

            aes_key = base64.b64decode(decrypted_data_json["data"].get("key"))

            # 解密分块
            decrypted_chunks = 1
            cipher = AES.new(aes_key, AES.MODE_CFB, iv=iv)  # 初始化 cipher

            with open(file_path, "wb") as out_file:
                while decrypted_chunks <= total_chunks:
                    progress_bar.value = decrypted_chunks / total_chunks
                    progress_info.value = (
                        f"正在解密分块 [{decrypted_chunks}/{total_chunks}]"
                    )
                    page.update()

                    chunk_file_path = os.path.join(
                        downloading_path, str(decrypted_chunks - 1)
                    )

                    with open(chunk_file_path, "rb") as chunk_file:
                        encrypted_chunk = chunk_file.read()
                        decrypted_chunk = cipher.decrypt(encrypted_chunk)
                        out_file.write(decrypted_chunk)

                    # os.remove(chunk_file_path)
                    decrypted_chunks += 1

            # 删除临时文件夹
            progress_bar.value = None
            progress_info.value = f"正在删除临时文件"
            page.update()

            shutil.rmtree(downloading_path)

        except Exception as e:
            send_error(page, f"Error receiving file: {e}")
            raise

        # 校验文件
        progress_bar.value = None
        progress_info.value = f"正在校验文件"
        page.update()

        def _action_verify():

            if file_size != os.path.getsize(file_path):
                send_error(
                    page,
                    f"File size mismatch: expected {file_size}, got {os.path.getsize(file_path)}",
                )
                return

            # 校验 SHA256
            actual_sha256 = calculate_sha256(file_path)
            if sha256 and actual_sha256 != sha256:
                send_error(
                    page,
                    f"SHA256 mismatch: expected {sha256}, got {actual_sha256}",
                )
                return

            return True

        if not _action_verify():
            os.remove(file_path)

        page.overlay.remove(progress_column)
        page.update()
        page.logger.info(f"File {file_path} received successfully.")

        download_lock.release()

    except Exception as e:
        send_error(page, traceback.format_exc())
        raise

    websocket.close()


def upload_file_to_server(
    page: ft.Page, task_id: str, file_path: str, refresh=True
) -> None:

    upload_lock: threading.Lock = page.session.get("upload_lock")
    if not upload_lock.acquire(timeout=0):
        send_error(page, "不能同时执行多个上传任务")
        return

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        try:
            websocket = connect(
                page.session.get("server_uri"), ssl=ssl_context, open_timeout=2
            )
        except (TimeoutError, websockets.exceptions.ConnectionClosedError):
            upload_lock.release()
            raise

        websocket.send(
            json.dumps(
                {
                    "action": "upload_file",
                    "data": {"task_id": task_id},
                },
                ensure_ascii=False,
            )
        )

        # Receive file metadata from the server
        response = json.loads(websocket.recv())
        if response["action"] != "transfer_file":
            page.logger.error("Invalid action received for file transfer.")
            return

        file_size = os.path.getsize(file_path)

        # if not file_size:
        #     upload_lock.release()
        #     raise ValueError("不能上传空文件")

        sha256 = calculate_sha256(file_path) if file_size else None

        task_info = {
            "action": "transfer_file",
            "data": {
                "sha256": sha256,
                "file_size": file_size,
            },
        }
        websocket.send(json.dumps(task_info, ensure_ascii=False))

        received_response = websocket.recv()
        if received_response not in ["ready", "stop"]:
            upload_lock.release()
            page.logger.error(
                f"Server did not acknowledge readiness for file transfer: {received_response}"
            )
            return

        
        if received_response == "ready":
            page.logger.info("File transmission begin.")

            try:
                progress_bar = ft.ProgressBar()
                progress_info = ft.Text(text_align="center", color=ft.Colors.WHITE)
                progress_column = ft.Column(
                    controls=[progress_bar, progress_info],
                    alignment=(
                        ft.MainAxisAlignment.START
                        if os.name == "nt"
                        else ft.MainAxisAlignment.END
                    ),
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
                page.overlay.append(progress_column)
                # page.overlay.append(progress_bar)
                page.update()

                chunk_size = 8192
                with open(file_path, "rb") as f:
                    while True:
                        # print("loop")
                        chunk = f.read(chunk_size)
                        websocket.send(chunk)

                        progress_bar.value = f.tell() / file_size
                        progress_info.value = f"{f.tell() / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                        page.update()

                        if not chunk or len(chunk) < chunk_size:
                            break

                page.overlay.remove(progress_column)
                page.update()
                page.logger.info(f"File {file_path} sent successfully.")
            except:
                raise
            
        upload_lock.release()
        load_directory: function = page.session.get("load_directory")
        current_directory_id = page.session.get("current_directory_id")
        if refresh:
            load_directory(page, current_directory_id)        

        websocket.close()

    except Exception as e:
        upload_lock.release()
        raise NotImplementedError
