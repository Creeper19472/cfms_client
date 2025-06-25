# type: ignore
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection


@route('settings')
class SettingsModel(Model):
    pass