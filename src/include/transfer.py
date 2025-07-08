# type: ignore
import flet as ft
import json
import base64, time
import os, sys

# from Crypto.Cipher import AES
from include.log import getCustomLogger
from common.notifications import send_error
import mmap, hashlib, ssl
from websockets.sync.client import connect
import threading


def calculate_sha256(file_path):
    # 使用更快的 hashlib 工具和内存映射文件
    with open(file_path, "rb") as f:
        # 使用内存映射文件直接映射到内存
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()


def receive_file_from_server(page: ft.Page, task_id: str, filename: str=None) -> None:
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
        websocket = connect(page.session.get("server_uri"), ssl=ssl_context)
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

    sha256 = response["data"].get("sha256")
    file_size = response["data"].get("file_size")

    websocket.send("ready")

    file_path = f"./{filename if filename else sha256[0:17]}"

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

        with open(file_path, "wb") as f:
            while True:
                # Receive encrypted data from the server
                data = websocket.recv()
                f.write(data)
                progress_bar.value = f.tell() / file_size
                progress_info.value = (
                    f"{f.tell() / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                )
                page.update()

                if not data or len(data) < 8192:
                    break

        # # Write the decrypted file to disk
        # file_path = f"received_{task_id}.bin"
        # with open(file_path, "wb") as f:
        #     f.write(decrypted_data)

        # Verify file size
        actual_size = os.path.getsize(file_path)
        if actual_size != file_size:
            page.logger.error(
                f"File size mismatch: expected {file_size}, got {actual_size}"
            )
            os.remove(file_path)
            return

        # Verify SHA256
        actual_sha256 = calculate_sha256(file_path)
        if sha256 and actual_sha256 != sha256:
            page.logger.error(
                f"SHA256 mismatch: expected {sha256}, got {actual_sha256}"
            )
            os.remove(file_path)
            return

        page.overlay.remove(progress_column)
        page.update()
        page.logger.info(f"File {file_path} received successfully.")

        download_lock.release()

    except:
        raise

    websocket.close()


def upload_file_to_server(page: ft.Page, task_id: str, file_path: str) -> None:

    upload_lock: threading.Lock = page.session.get("upload_lock")
    if not upload_lock.acquire(timeout=0):
        send_error(page, "不能同时上传多个文件")
        return

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        websocket = connect(page.session.get("server_uri"), ssl=ssl_context)
    except Exception as e:
        upload_lock.release()
        raise NotImplementedError
    
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

    sha256 = calculate_sha256(file_path)
    file_size = os.path.getsize(file_path)

    task_info = {
        "action": "transfer_file",
        "data": {
            "sha256": sha256,
            "file_size": file_size,
        },
    }
    websocket.send(json.dumps(task_info, ensure_ascii=False))
    
    received_response = websocket.recv()
    if received_response != "ready":
        page.logger.error(
            f"Server did not acknowledge readiness for file transfer: {received_response}"
        )
        return

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
                progress_info.value = (
                    f"{f.tell() / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                )
                page.update()

                if not chunk or len(chunk) < chunk_size:
                    break

        page.overlay.remove(progress_column)
        page.update()
        page.logger.info(f"File {file_path} sent successfully.")

        upload_lock.release()
        load_directory: function = page.session.get("load_directory")
        current_directory_id = page.session.get("current_directory_id")
        load_directory(page, current_directory_id)

    except:
        raise

    websocket.close()