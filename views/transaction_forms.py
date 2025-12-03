import flet as ft
from database import ActivityLog
import datetime

class TransactionFormDialog(ft.AlertDialog):
    def __init__(self, page, on_success, log=None):
        super().__init__()
        self.page = page
        self.on_success = on_success
        self.log = log
        self.title = ft.Text("Add Transaction" if not log else "Edit Transaction")
        
        self.action_field = ft.Dropdown(
            label="Action",
            options=[
                ft.dropdown.Option("Usage"),
                ft.dropdown.Option("Restock"),
                ft.dropdown.Option("Purchase"),
                ft.dropdown.Option("Adjustment"),
                ft.dropdown.Option("Other"),
            ],
            value=log.action if log else "Usage"
        )
        self.details_field = ft.TextField(label="Details", value=log.details if log else "", multiline=True)
        self.cost_field = ft.TextField(label="Value (PKR)", value=str(log.cost) if log else "0.0", keyboard_type=ft.KeyboardType.NUMBER)
        
        self.content = ft.Column(
            [
                self.action_field,
                self.details_field,
                self.cost_field,
            ],
            tight=True,
            width=400
        )
        
        self.actions = [
            ft.TextButton("Cancel", on_click=self.close),
            ft.ElevatedButton("Save", on_click=self.save)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def close(self, e):
        self.page.close(self)

    def save(self, e):
        try:
            data = {
                "action": self.action_field.value,
                "details": self.details_field.value,
                "cost": float(self.cost_field.value) if self.cost_field.value else 0.0,
                "timestamp": datetime.datetime.now() if not self.log else self.log.timestamp # Keep original time on edit, or update? Let's keep original.
            }
            
            if self.log:
                query = ActivityLog.update(**data).where(ActivityLog.id == self.log.id)
                query.execute()
            else:
                ActivityLog.create(**data)
            
            self.close(None)
            self.on_success()
            
        except Exception as ex:
            print(f"Error saving transaction: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()
