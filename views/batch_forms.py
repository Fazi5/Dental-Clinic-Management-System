import flet as ft
from database import Batch, InventoryItem
import datetime

class BatchFormDialog(ft.AlertDialog):
    def __init__(self, page, on_success, batch):
        super().__init__()
        self.page = page
        self.on_success = on_success
        self.batch = batch
        self.title = ft.Text(f"Edit Batch #{batch.id}")
        
        self.quantity_field = ft.TextField(label="Quantity", value=str(batch.quantity), keyboard_type=ft.KeyboardType.NUMBER)
        self.cost_field = ft.TextField(label="Cost per Unit", value=str(batch.cost_per_unit), keyboard_type=ft.KeyboardType.NUMBER)
        self.details_field = ft.TextField(label="Details", value=batch.details or "", multiline=True)
        
        # Date Pickers
        self.expiry_date_field = ft.TextField(label="Expiry Date", value=str(batch.expiry_date) if batch.expiry_date else "", read_only=True)
        self.purchase_date_field = ft.TextField(label="Purchase Date", value=str(batch.purchase_date) if batch.purchase_date else "", read_only=True)
        
        def pick_expiry_date(e):
            self.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime(2020, 1, 1),
                    last_date=datetime.datetime(2030, 12, 31),
                    on_change=lambda e: self.set_date(self.expiry_date_field, e.control.value)
                )
            )

        def pick_purchase_date(e):
            self.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime(2020, 1, 1),
                    last_date=datetime.datetime(2030, 12, 31),
                    on_change=lambda e: self.set_date(self.purchase_date_field, e.control.value)
                )
            )
        self.content = ft.Column([
            self.quantity_field,
            self.cost_field,
            self.details_field,
            ft.Row([
                self.purchase_date_field,
                ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_purchase_date)
            ]),
            ft.Row([
                self.expiry_date_field,
                ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_expiry_date)
            ])
        ], tight=True, width=400)
        
        self.actions = [
            ft.TextButton("Cancel", on_click=self.close),
            ft.ElevatedButton("Save", on_click=self.save)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def set_date(self, field, date_val):
        if date_val:
            field.value = date_val.strftime("%Y-%m-%d")
            field.update()

    def close(self, e):
        self.page.close(self)

    def save(self, e):
        try:
            # Update Batch
            self.batch.quantity = int(self.quantity_field.value)
            self.batch.cost_per_unit = float(self.cost_field.value)
            self.batch.details = self.details_field.value
            
            if self.expiry_date_field.value:
                self.batch.expiry_date = self.expiry_date_field.value
            else:
                self.batch.expiry_date = None
                
            if self.purchase_date_field.value:
                self.batch.purchase_date = self.purchase_date_field.value
            
            self.batch.save()
            
            # Update Item Total Quantity
            # Recalculate total from all batches to be safe
            total_qty = 0
            for b in self.batch.item.batches:
                total_qty += b.quantity
            
            self.batch.item.quantity = total_qty
            self.batch.item.save()
            
            self.close(None)
            self.on_success()
            
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Invalid input"))
            self.page.snack_bar.open = True
            self.page.update()
