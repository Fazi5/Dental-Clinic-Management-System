import flet as ft
from database import InventoryItem

class ItemFormDialog(ft.AlertDialog):
    def __init__(self, page, on_success, item=None):
        super().__init__()
        self.page = page
        self.on_success = on_success
        self.item = item # If item is provided, it's an edit
        self.title = ft.Text("Add Item" if not item else "Edit Item")
        
        self.name_field = ft.TextField(label="Name", value=item.name if item else "")
        self.category_field = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Equipment"),
                ft.dropdown.Option("Instrument"),
                ft.dropdown.Option("Consumable"),
            ],
            value=item.category if item else "Consumable"
        )
        self.quantity_field = ft.TextField(label="Quantity", value=str(item.quantity) if item else "0", keyboard_type=ft.KeyboardType.NUMBER)
        self.unit_field = ft.TextField(label="Unit", value=item.unit if item else "pcs")
        self.cost_field = ft.TextField(label="Cost per Unit (PKR)", value=str(item.cost_per_unit) if item else "0.0", keyboard_type=ft.KeyboardType.NUMBER)
        self.min_stock_field = ft.TextField(label="Min Stock", value=str(item.min_stock) if item else "5", keyboard_type=ft.KeyboardType.NUMBER)
        self.expiry_date_field = ft.TextField(label="Expiry Date (YYYY-MM-DD)", value=str(item.expiry_date) if item and item.expiry_date else "", hint_text="YYYY-MM-DD")
        self.sterilization_status_field = ft.Dropdown(
            label="Sterilization Status",
            options=[
                ft.dropdown.Option("Sterile"),
                ft.dropdown.Option("Used"),
                ft.dropdown.Option("In-Autoclave"),
            ],
            value=item.sterilization_status if item else "Sterile"
        )
        
        self.acquisition_type_field = ft.Dropdown(
            label="Acquisition Type",
            options=[
                ft.dropdown.Option("New Purchase"),
                ft.dropdown.Option("Opening Stock"),
            ],
            value="New Purchase",
            visible=not item # Only visible for new items
        )
        
        self.content = ft.Column(
            [
                self.name_field,
                self.category_field,
                self.quantity_field,
                self.unit_field,
                self.cost_field,
                self.min_stock_field,
                self.expiry_date_field,
                self.sterilization_status_field,
                self.acquisition_type_field,
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
            expiry_val = self.expiry_date_field.value if self.expiry_date_field.value else None
            
            data = {
                "name": self.name_field.value,
                "category": self.category_field.value,
                "quantity": int(self.quantity_field.value),
                "unit": self.unit_field.value,
                "cost_per_unit": float(self.cost_field.value) if self.cost_field.value else 0.0,
                "min_stock": int(self.min_stock_field.value),
                "expiry_date": expiry_val,
                "sterilization_status": self.sterilization_status_field.value
            }
            
            if self.item:
                query = InventoryItem.update(**data).where(InventoryItem.id == self.item.id)
                query.execute()
            else:
                item = InventoryItem.create(**data)
                # Log initial acquisition
                acq_type = self.acquisition_type_field.value
                cost = data["cost_per_unit"] * data["quantity"]
                from database import ActivityLog # Import here to avoid circular dependency if any
                ActivityLog.create(
                    action=acq_type, 
                    details=f"Added {data['quantity']} {data['unit']} of {data['name']}", 
                    cost=cost
                )
            
            self.close(None)
            self.on_success()
            
        except Exception as ex:
            print(f"Error saving item: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()
