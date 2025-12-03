import flet as ft
from components.app_layout import AppLayout
from views.dashboard import DashboardView
from views.inventory import InventoryView
from views.suppliers import SupplierView
from views.sterilization import SterilizationView
from views.transactions import TransactionsView
from database import initialize_db

def main(page: ft.Page):
    initialize_db()
    page.title = "Dental Clinic Storage Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_icon = "app-icon.png"
    
    # "Clean Clinical" Theme Colors
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.TEAL_600,
            primary_container=ft.Colors.TEAL_100,
            secondary=ft.Colors.CYAN_600,
            surface=ft.Colors.WHITE,
            background=ft.Colors.GREY_50,
        )
    )

    def on_nav_change(index):
        if index == 0:
            layout.set_content(DashboardView(on_navigate=navigate_to))
        elif index == 1:
            layout.set_content(InventoryView())
        elif index == 2:
            layout.set_content(SupplierView())
        elif index == 3:
            layout.set_content(SterilizationView())
        elif index == 4:
            layout.set_content(TransactionsView())

    def navigate_to(index):
        layout.sidebar.selected_index = index
        layout.sidebar.update()
        on_nav_change(index)

    layout = AppLayout(page, on_nav_change, DashboardView(on_navigate=navigate_to))
    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main)
