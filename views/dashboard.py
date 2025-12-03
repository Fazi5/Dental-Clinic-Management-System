import flet as ft
from database import InventoryItem, Supplier, ActivityLog

class DashboardView(ft.Column):
    def __init__(self, on_navigate=None):
        super().__init__()
        self.on_navigate = on_navigate
        self.scroll = ft.ScrollMode.AUTO
        self.controls = [
            ft.Text("Dashboard", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            self.build_summary_cards(),
            ft.Divider(),
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Recent Activity", size=20, weight=ft.FontWeight.BOLD),
                            self.build_activity_log(limit=10)
                        ],
                        expand=True
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        [
                            ft.Text("New Purchases", size=20, weight=ft.FontWeight.BOLD),
                            self.build_purchase_log(limit=10)
                        ],
                        expand=True
                    )
                ],
                expand=True
            )
        ]

    def build_activity_log(self, limit=10):
        logs = ActivityLog.select().order_by(ActivityLog.timestamp.desc()).limit(limit)
        
        if logs.count() == 0:
            return ft.Text("No recent activity.", italic=True)

        return ft.ListView(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.HISTORY),
                    title=ft.Text(log.details),
                    subtitle=ft.Text(f"{log.action} - {log.timestamp.strftime('%Y-%m-%d %H:%M')}"),
                ) for log in logs
            ],
            height=300,
            spacing=10
        )

    def build_purchase_log(self, limit=10):
        # Filter for "Purchase" or "New Purchase"
        logs = ActivityLog.select().where(
            (ActivityLog.action == "Purchase") | (ActivityLog.action == "New Purchase")
        ).order_by(ActivityLog.timestamp.desc()).limit(limit)
        
        if logs.count() == 0:
            return ft.Text("No recent purchases.", italic=True)

        return ft.ListView(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.SHOPPING_CART, color=ft.Colors.GREEN),
                    title=ft.Text(log.details),
                    subtitle=ft.Text(f"PKR {log.cost:.2f}" if log.cost else "-"),
                    trailing=ft.Text(log.timestamp.strftime('%Y-%m-%d'), size=12),
                ) for log in logs
            ],
            height=300,
            spacing=10
        )

    def build_summary_cards(self):
        total_items = InventoryItem.select().count()
        low_stock = InventoryItem.select().where(InventoryItem.quantity < InventoryItem.min_stock).count()
        suppliers = Supplier.select().count()

        return ft.Row(
            [
                self.summary_card("Total Items", str(total_items), ft.Icons.INVENTORY, ft.Colors.BLUE_100, ft.Colors.TEAL, 1),
                self.summary_card("Low Stock", str(low_stock), ft.Icons.WARNING, ft.Colors.RED_100, ft.Colors.RED, 1),
                self.summary_card("Suppliers", str(suppliers), ft.Icons.PEOPLE, ft.Colors.GREEN_100, ft.Colors.TEAL, 2),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )

    def summary_card(self, title, value, icon, bg_color, icon_color, nav_index):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=40, color=icon_color),
                    ft.Text(value, size=30, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=16),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=200,
            height=150,
            bgcolor=bg_color,
            border_radius=10,
            padding=20,
            on_click=lambda e: self.on_navigate(nav_index) if self.on_navigate else None,
            ink=True,
        )
