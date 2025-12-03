import flet as ft
from components.sidebar import Sidebar

class AppLayout(ft.Row):
    def __init__(self, page, on_nav_change, initial_content):
        super().__init__()
        self.page = page
        self.sidebar = Sidebar(page, on_nav_change)
        self.content_area = ft.Container(content=initial_content, expand=True, padding=20)
        self.expand = True
        
        self.controls = [
            self.sidebar,
            ft.VerticalDivider(width=1),
            self.content_area
        ]

    def set_content(self, content):
        self.content_area.content = content
        self.content_area.update()
