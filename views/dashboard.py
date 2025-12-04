import flet as ft
import datetime
from database import InventoryItem, Supplier, ActivityLog, LabCase
from utils.notifications import NotificationManager

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
                            ft.Text("Transactions", size=20, weight=ft.FontWeight.BOLD),
                            self.build_transaction_log(limit=10)
                        ],
                        expand=True
                    )
                ],
                expand=True
            )
        ]
        
    def did_mount(self):
        # Trigger Notification Check on Load (Every 3 hours)
        last_check_str = self.page.session.get("dashboard_last_alert_time")
        should_check = False
        
        if not last_check_str:
            should_check = True
        else:
            try:
                last_check = datetime.datetime.fromisoformat(last_check_str)
                if datetime.datetime.now() - last_check > datetime.timedelta(hours=3):
                    should_check = True
            except:
                should_check = True # Invalid format, reset

        if should_check:
            NotificationManager().check_and_notify()
            self.page.session.set("dashboard_last_alert_time", datetime.datetime.now().isoformat())

    def get_action_icon(self, action):
        if action in ["Purchase", "New Purchase", "Restock", "Stock Added"]:
            return ft.Icons.ADD_SHOPPING_CART
        elif action in ["Sale"]:
            return ft.Icons.MONETIZATION_ON
        elif action in ["Usage", "Used", "Consumed"]:
            return ft.Icons.REMOVE_SHOPPING_CART
        elif action == "Sterilization":
            return ft.Icons.CLEANING_SERVICES
        elif action == "Labworks":
            return ft.Icons.MEDICAL_SERVICES
        else:
            return ft.Icons.HISTORY

    def build_activity_log(self, limit=10):
        # Filter out purely financial transactions if desired, or show everything?
        # User wants "Recent Activity" to match logic in modules.
        # So we show everything but formatted nicely.
        logs = ActivityLog.select().order_by(ActivityLog.timestamp.desc()).limit(limit)
        
        if logs.count() == 0:
            return ft.Text("No recent activity.", italic=True)

        return ft.ListView(
            [
                ft.ListTile(
                    leading=ft.Container(
                        content=ft.Icon(self.get_action_icon(log.action), color=ft.Colors.WHITE, size=16),
                        bgcolor=self.get_action_color(log.action),
                        width=30, height=30, border_radius=15, alignment=ft.alignment.center
                    ),
                    title=ft.Text(log.details, size=14),
                    subtitle=ft.Text(f"{log.action} • {log.timestamp.strftime('%Y-%m-%d %H:%M')}", size=12),
                ) for log in logs
            ],
            height=300,
            spacing=5
        )

    def get_action_color(self, action):
        if action in ["Purchase", "New Purchase", "Restock", "Stock Added"]:
            return ft.Colors.RED
        elif action in ["Sale"]:
            return ft.Colors.GREEN
        elif action in ["Usage", "Used", "Consumed"]:
            return ft.Colors.ORANGE
        elif action == "Sterilization":
            return ft.Colors.BLUE
        elif action == "Labworks":
            return ft.Colors.PURPLE
        else:
            return ft.Colors.GREY

    def build_transaction_log(self, limit=10):
        # Filter out Sterilization events and zero-cost Usage events (Same as TransactionsView)
        logs = ActivityLog.select().where(
            (ActivityLog.action != "Sterilization") & 
            (~((ActivityLog.action == "Usage") & (ActivityLog.cost == 0))) &
            (~((ActivityLog.action == "Used") & (ActivityLog.cost == 0)))
        ).order_by(ActivityLog.timestamp.desc()).limit(limit)
        
        if logs.count() == 0:
            return ft.Text("No recent transactions.", italic=True)

        return ft.ListView(
            [
                ft.ListTile(
                    leading=ft.Container(
                        content=ft.Text(log.action[:1], color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=self.get_action_color(log.action),
                        width=30, height=30, border_radius=15, alignment=ft.alignment.center
                    ),
                    title=ft.Text(log.details),
                    subtitle=ft.Text(f"{log.action} - {log.timestamp.strftime('%Y-%m-%d')}"),
                    trailing=ft.Text(
                        f"PKR {log.cost:,.2f}" if log.cost else "-",
                        color=self.get_action_color(log.action),
                        weight=ft.FontWeight.BOLD
                    ),
                ) for log in logs
            ],
            height=300,
            spacing=10
        )

    def build_summary_cards(self):
        total_items = InventoryItem.select().count()
        need_sterilization = InventoryItem.select().where(InventoryItem.quantity_used > 0).count()
        suppliers = Supplier.select().count()
        active_labworks = LabCase.select().where(LabCase.status == "Sent").count()

        return ft.Row(
            [
                self.summary_card("Items in Inventory", str(total_items), ft.Icons.INVENTORY, ft.Colors.BLUE_100, ft.Colors.TEAL, 1),
                self.summary_card("Need Sterilization", str(need_sterilization), ft.Icons.CLEANING_SERVICES, ft.Colors.RED_100, ft.Colors.RED, 3),
                self.summary_card("Suppliers", str(suppliers), ft.Icons.PEOPLE, ft.Colors.GREEN_100, ft.Colors.TEAL, 2),
                self.summary_card("Active Labworks", str(active_labworks), ft.Icons.MEDICAL_SERVICES, ft.Colors.ORANGE_100, ft.Colors.ORANGE, 5),
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
