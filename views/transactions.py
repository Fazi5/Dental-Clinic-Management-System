import flet as ft
from database import ActivityLog
from views.transaction_forms import TransactionFormDialog

class TransactionsView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.controls = [
            ft.Row([
                ft.Text("Transaction & Billing Log", size=30, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.ADD, on_click=self.add_transaction_click)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_data_table(self):
        logs = ActivityLog.select().order_by(ActivityLog.timestamp.desc())
        
        return ft.DataTable(
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
                        ft.DataCell(ft.Text(log.action)),
                        ft.DataCell(ft.Text(log.details)),
                        ft.DataCell(ft.Text(f"PKR {log.cost:.2f}" if log.cost else "-")),
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
        self.controls[-1] = self.build_data_table()
        self.update()
