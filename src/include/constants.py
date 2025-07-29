import os

__all__ = ["RUNTIME_PATH", "FLET_APP_STORAGE_TEMP"]

RUNTIME_PATH = os.environ.get("PYTHONHOME", "")
FLET_APP_STORAGE_TEMP = os.environ.get("FLET_APP_STORAGE_TEMP", ".")
