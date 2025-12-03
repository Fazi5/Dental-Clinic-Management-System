import flet as ft

class Sidebar(ft.NavigationRail):
    def __init__(self, page, on_nav_change):
        super().__init__()
        self.page = page
        self.on_nav_change = on_nav_change # Callback for navigation
        self.label_type = ft.NavigationRailLabelType.ALL
        self.min_width = 100
        self.min_extended_width = 400
        self.group_alignment = -0.9
        self.destinations = [
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                selected_icon=ft.Icons.INVENTORY_2,
                label="Inventory",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Suppliers",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CLEANING_SERVICES_OUTLINED,
                selected_icon=ft.Icons.CLEANING_SERVICES,
                label="Sterilization",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                selected_icon=ft.Icons.RECEIPT_LONG,
                label="Transactions",
            ),
        ]
        self.on_change = self.nav_change

    def nav_change(self, e):
        self.on_nav_change(e.control.selected_index)
