# type: ignore
import flet as ft
import json
import base64
import os
# from Crypto.Cipher import AES
from include.log import getCustomLogger
import mmap, hashlib


def calculate_sha256(file_path):
    # 使用更快的 hashlib 工具和内存映射文件
    with open(file_path, "rb") as f:
        # 使用内存映射文件直接映射到内存
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()


def receive_file_from_server(page: ft.Page, task_id: str) -> None:
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
    # Send the request for file metadata
    page.websocket.send(
        json.dumps(
            {
                "action": "download_file",
                "data": {"task_id": task_id},
            },
            ensure_ascii=False,
        )
    )

    # Receive file metadata from the server
    response = json.loads(page.websocket.recv())
    if response["action"] != "transfer_file":
        page.logger.error("Invalid action received for file transfer.")
        return

    sha256 = response["data"].get("sha256")
    file_size = response["data"].get("file_size")

    page.websocket.send("ready")

    file_path = f"./{sha256[0:17]}"

    try:
        progress_bar = ft.ProgressBar(width=page.width)
        progress_info = ft.Text(text_align="center", color=ft.Colors.WHITE)
        progress_column = ft.Column(controls=[progress_bar, progress_info], width=page.width, alignment=
                                    ft.MainAxisAlignment.START, horizontal_alignment=
                                    ft.CrossAxisAlignment.CENTER)
        page.overlay.append(progress_column)
        # page.overlay.append(progress_bar)
        page.update()

        with open(file_path, "wb") as f:     
            while True:
                # Receive encrypted data from the server
                data = page.websocket.recv()
                f.write(data)
                progress_bar.value = f.tell() / file_size
                progress_info.value = f"{f.tell() / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
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

    except:
        raise
