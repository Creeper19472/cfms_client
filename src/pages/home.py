# type: ignore
import flet as ft
from flet_model import Model, route
from websockets import ClientConnection

# Enhanced Colors & Styles
PRIMARY_COLOR = "#4f46e5"  # Deep indigo for primary actions
PLACEHOLDER_COLOR = "#9ca3af"  # Softer neutral for hint text
FIELD_BG = "#1f2937"  # Dark slate for input fields
BORDER_COLOR = "#374151"  # Neutral border with good contrast
TEXT_COLOR = "#f3f4f6"  # Near-white for clarity
ERROR_COLOR = "#f87171"  # Softer red for errors
SUCCESS_COLOR = "#34d399"  # Minty green for success
BUTTON_RADIUS = 12  # Slightly smaller for a sharper modern look
FORM_WIDTH = 380


@route('home')
class HomeModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    # UI Components
    appbar = ft.AppBar(
        title=ft.Text("Home"),
        center_title=True,
        # bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
    )

    home_view = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("落霞与孤鹜齐飞，秋水共长天一色。", size=22),
                        ]
                    ),
                    margin=10,
                    padding=10,
                    alignment=ft.alignment.center,
                    visible=True,
                )
    
    profile_view = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Welcome to Profile Page", size=22),
                        ]
                    ),
                    margin=10,
                    padding=10,
                    alignment=ft.alignment.center,
                    visible=False,
                )

    messages_view = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Welcome to Messages Page", size=22),
                        ]
                    ),
                    margin=10,
                    padding=10,
                    alignment=ft.alignment.center,
                    visible=False,
                )

    navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profile"),
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.MESSAGE, label="Messages"),
        ],
        selected_index=1,
        on_change="handle_navigation",
    )

    controls = [
        home_view,
        profile_view,
        messages_view,
        navigation_bar,
    ]

    def navigate_to_login(self, e):
        self.page.go('/login')

    def handle_navigation(self, e):
        """
        Handle changes in navigation bar and update the page 
        accordingly by hiding/showing the container related to the selection
        in this case we have only three navigation destination
        
        1- Profile (index 0)
        2- Home (index 1) selected by default 
        3- message (index 2)
        """
        if e.data == '0':#Profile selected
            self.messages_view.visible = False
            self.profile_view.visible = True
            self.home_view.visible = False

        elif e.data == '1':#Home selected
            print("in Home view")
            self.messages_view.visible = False
            self.profile_view.visible = False
            self.home_view.visible = True
        
        elif e.data == '2':#Messages selected
            print("in Messages view")
            self.messages_view.visible = True
            self.profile_view.visible = False
            self.home_view.visible = False

        self.update()
    