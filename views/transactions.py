import flet as ft
from database import ActivityLog
from views.transaction_forms import TransactionFormDialog

from utils.data_handler import export_to_csv, export_to_pdf, import_from_csv

class TransactionsView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.export_csv_dialog = ft.FilePicker(on_result=self.export_csv_result)
        self.export_pdf_dialog = ft.FilePicker(on_result=self.export_pdf_result)
        self.import_csv_dialog = ft.FilePicker(on_result=self.import_csv_result)

        self.controls = [
            self.export_csv_dialog,
            self.export_pdf_dialog,
            self.import_csv_dialog,
            
            ft.Row([
                ft.Text("Transaction & Billing Log", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(text="Export CSV", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self.export_csv_dialog.save_file(allowed_extensions=["csv"], file_name="transactions.csv")),
                            ft.PopupMenuItem(text="Export PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: self.export_pdf_dialog.save_file(allowed_extensions=["pdf"], file_name="transactions.pdf")),
                            ft.PopupMenuItem(text="Import CSV", icon=ft.Icons.UPLOAD, on_click=lambda _: self.import_csv_dialog.pick_files(allowed_extensions=["csv"])),
                        ]
                    ),
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_transaction_click)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_summary_cards(),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_summary_cards(self):
        # Calculate totals
        total_expenses = 0.0
        total_usage = 0.0
        total_sales = 0.0
        
        logs = ActivityLog.select()
        for log in logs:
            if log.cost:
                if log.action in ["Purchase", "New Purchase", "Restock", "Stock Added"]:
                    total_expenses += log.cost
                elif log.action in ["Usage", "Used", "Consumed"]:
                    total_usage += log.cost
                elif log.action in ["Sale"]:
                    total_sales += log.cost

        return ft.Row(
            [
                self.summary_card("Total Purchases (Inflow)", f"PKR {total_expenses:,.2f}", ft.Icons.ADD_SHOPPING_CART, ft.Colors.RED_100, ft.Colors.RED),
                self.summary_card("Total Usage (Cost)", f"PKR {total_usage:,.2f}", ft.Icons.REMOVE_SHOPPING_CART, ft.Colors.ORANGE_100, ft.Colors.ORANGE),
                self.summary_card("Total Sales (Revenue)", f"PKR {total_sales:,.2f}", ft.Icons.MONETIZATION_ON, ft.Colors.GREEN_100, ft.Colors.GREEN),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )

    def summary_card(self, title, value, icon, bg_color, icon_color):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=30, color=icon_color),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=14),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=250,
            height=120,
            bgcolor=bg_color,
            border_radius=10,
            padding=20,
        )

    def build_data_table(self):
        # Filter out Sterilization events and zero-cost Usage events
        logs = ActivityLog.select().where(
            (ActivityLog.action != "Sterilization") & 
            (~((ActivityLog.action == "Usage") & (ActivityLog.cost == 0))) &
            (~((ActivityLog.action == "Used") & (ActivityLog.cost == 0)))
        ).order_by(ActivityLog.timestamp.desc())
        
        return ft.ListView(
            [
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Date")),
                        ft.DataColumn(ft.Text("Action")),
                        ft.DataColumn(ft.Text("Details")),
                        ft.DataColumn(ft.Text("Value"), numeric=True),
                        ft.DataColumn(ft.Text("Actions")),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(log.timestamp.strftime("%Y-%m-%d %H:%M"))),
                                ft.DataCell(
                                    ft.Container(
                                        content=ft.Text(log.action, color=ft.Colors.WHITE, size=12),
                                        bgcolor=self.get_action_color(log.action),
                                        padding=5, border_radius=5
                                    )
                                ),
                                ft.DataCell(ft.Text(log.details)),
                                ft.DataCell(
                                    ft.Text(
                                        f"PKR {log.cost:,.2f}" if log.cost else "-",
                                        color=self.get_action_color(log.action),
                                        weight=ft.FontWeight.BOLD
                                    )
                                ),
                                ft.DataCell(
                                    ft.Row([
                                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, l=log: self.edit_transaction_click(e, l)),
                                        ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, l=log: self.delete_transaction_click(e, l))
                                    ])
                                ),
                            ]
                        ) for log in logs
                    ],
                    width=float('inf'),
                )
            ],
            expand=True,
            spacing=10,
        )

    def get_action_color(self, action):
        if action in ["Purchase", "New Purchase", "Restock", "Stock Added"]:
            return ft.Colors.RED
        elif action in ["Sale"]:
            return ft.Colors.GREEN
        elif action in ["Usage", "Used", "Consumed"]:
            return ft.Colors.ORANGE # Usage is a cost/consumption, distinct from direct expense but still negative
        elif action == "Sterilization":
            return ft.Colors.BLUE
        else:
            return ft.Colors.GREY

    def add_transaction_click(self, e):
        dialog = TransactionFormDialog(e.page, self.refresh_table)
        e.page.open(dialog)

    def edit_transaction_click(self, e, log):
        dialog = TransactionFormDialog(e.page, self.refresh_table, log)
        e.page.open(dialog)

    def delete_transaction_click(self, e, log):
        def confirm_delete(e):
            log.delete_instance()
            self.refresh_table()
            e.page.close(dialog)
            e.page.snack_bar = ft.SnackBar(ft.Text("Deleted transaction record"))
            e.page.snack_bar.open = True
            e.page.update()

        def cancel_delete(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this record?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def refresh_table(self):
        self.controls = [
            self.export_csv_dialog,
            self.export_pdf_dialog,
            self.import_csv_dialog,
            ft.Row([
                ft.Text("Transaction & Billing Log", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(text="Export CSV", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self.export_csv_dialog.save_file(allowed_extensions=["csv"], file_name="transactions.csv")),
                            ft.PopupMenuItem(text="Export PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: self.export_pdf_dialog.save_file(allowed_extensions=["pdf"], file_name="transactions.pdf")),
                            ft.PopupMenuItem(text="Import CSV", icon=ft.Icons.UPLOAD, on_click=lambda _: self.import_csv_dialog.pick_files(allowed_extensions=["csv"])),
                        ]
                    ),
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_transaction_click)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_summary_cards(),
            ft.Divider(),
            self.build_data_table()
        ]
        self.update()

    def export_csv_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = ActivityLog.select()
            fields = ["timestamp", "action", "details", "cost"]
            success, msg = export_to_csv(query, e.path, fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def export_pdf_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = ActivityLog.select()
            fields = ["timestamp", "action", "details", "cost"]
            success, msg = export_to_pdf(query, e.path, "Transaction Report", fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def import_csv_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            field_map = {
                "timestamp": "timestamp",
                "action": "action",
                "details": "details",
                "cost": "cost"
            }
            success, msg = import_from_csv(ActivityLog, e.files[0].path, field_map)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()
            self.refresh_table()
