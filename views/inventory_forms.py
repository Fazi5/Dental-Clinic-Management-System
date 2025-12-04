import flet as ft
from database import InventoryItem
import datetime

class ItemFormDialog(ft.AlertDialog):
    def __init__(self, page, on_success, item=None):
        super().__init__()
        self.page = page
        self.on_success = on_success
        self.item = item # If item is provided, it's an edit
        self.title = ft.Text("Add Item" if not item else "Edit Item")

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
        
        self.name_field = ft.TextField(label="Name", value=item.name if item else "")
        self.expiry_date_field = ft.TextField(
            label="Expiry Date (YYYY-MM-DD)", 
            value=str(item.expiry_date) if item and item.expiry_date else "", 
            hint_text="YYYY-MM-DD",
            visible=(item.category == "Consumable") if item else True # Default to visible or check default category
        )
        
        self.expiry_date_button = ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_expiry_date, visible=(item.category == "Consumable") if item else True)

        def on_category_change(e):
            is_consumable = (self.category_field.value == "Consumable")
            
            # Expiry Date Visibility
            self.expiry_date_field.visible = is_consumable
            self.expiry_date_button.visible = is_consumable
            
            # Min Stock Label
            self.min_stock_field.label = "Minimum Stock" if is_consumable else "Min Sterilized"
            
            # Sterilization Status Visibility
            self.sterilization_status_field.visible = not is_consumable
            
            # Purpose Visibility
            self.purpose_field.visible = is_consumable
            
            self.page.update()

        self.category_field = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Equipment"),
                ft.dropdown.Option("Instrument"),
                ft.dropdown.Option("Consumable"),
            ],
            value=item.category if item else "Consumable",
            on_change=on_category_change
        )
        
        self.quantity_field = ft.TextField(label="Quantity", value=str(item.quantity) if item else "0", keyboard_type=ft.KeyboardType.NUMBER)
        self.unit_field = ft.TextField(label="Unit", value=item.unit if item else "pcs")
        self.cost_field = ft.TextField(label="Cost per Unit (PKR)", value=str(item.cost_per_unit) if item else "0.0", keyboard_type=ft.KeyboardType.NUMBER)
        
        # Initial Label Logic
        initial_min_label = "Minimum Stock" if (not item or item.category == "Consumable") else "Min Sterilized"
        self.min_stock_field = ft.TextField(label=initial_min_label, value=str(item.min_stock) if item else "5", keyboard_type=ft.KeyboardType.NUMBER)
        
        # Initial Visibility Logic
        initial_sterilization_visible = (not item or item.category != "Consumable")
        # Wait, if default is Consumable (new item), then it should be HIDDEN initially?
        # User said "is sterlization status is needed for consumables" -> No.
        # Default category is "Consumable". So default visibility should be False.
        if not item:
            initial_sterilization_visible = False # Default category is Consumable
        
        self.sterilization_status_field = ft.Dropdown(
            label="Sterilization Status",
            options=[
                ft.dropdown.Option("Sterile"),
                ft.dropdown.Option("Used"),
            ],
            value=item.sterilization_status if item else "Sterile",
            visible=initial_sterilization_visible
        )
        
        # Purpose Field for Consumables
        initial_purpose_visible = (not item or item.category == "Consumable")
        self.purpose_field = ft.Dropdown(
            label="Purpose",
            options=[
                ft.dropdown.Option("Selling"),
                ft.dropdown.Option("Usage"),
            ],
            value=item.purpose if item and item.purpose else "Usage",
            visible=initial_purpose_visible
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
        
        self.details_field = ft.TextField(
            label="Batch Details (Company, Grade, etc.)", 
            multiline=True,
            visible=not item # Only visible for new items (initial batch)
        )
        
        self.purchase_date_field = ft.TextField(
            label="Purchase Date (YYYY-MM-DD)", 
            value=datetime.date.today().strftime("%Y-%m-%d"),
            read_only=True,
            visible=not item # Only visible for new items
        )
        
        # Ensure initial visibility is correct if creating new or editing
        if not item:
            self.expiry_date_field.visible = True # Default Consumable
            self.expiry_date_button.visible = True
        
        self.content = ft.Column(
            [
                self.name_field,
                self.category_field,
                self.quantity_field,
                self.unit_field,
                self.cost_field,
                self.min_stock_field,
                ft.Row([
                    self.purchase_date_field,
                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_purchase_date, visible=not item)
                ]),
                ft.Row([
                    self.expiry_date_field,
                    self.expiry_date_button
                ]),
                self.sterilization_status_field,
                self.purpose_field,
                self.acquisition_type_field,
                self.details_field,
            ],
            tight=True,
            width=400,
            scroll=ft.ScrollMode.AUTO,
            height=500
        )
        
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
            # Validation Logic
            required_fields = {
                "Name": self.name_field.value,
                "Quantity": self.quantity_field.value,
                "Unit": self.unit_field.value,
                "Cost": self.cost_field.value,
                "Min Stock": self.min_stock_field.value,
            }

            # Add conditional fields to validation
            if self.category_field.value == "Consumable" and self.expiry_date_field.visible:
                required_fields["Expiry Date"] = self.expiry_date_field.value
            
            if self.purchase_date_field.visible:
                required_fields["Purchase Date"] = self.purchase_date_field.value

            # Check for empty values
            missing_fields = [name for name, value in required_fields.items() if not value or str(value).strip() == ""]
            
            if missing_fields:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Please fill in: {', '.join(missing_fields)}"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Only save expiry date if category is Consumable
            expiry_val = None
            if self.category_field.value == "Consumable" and self.expiry_date_field.value:
                expiry_val = self.expiry_date_field.value
            
            data = {
                "name": self.name_field.value,
                "category": self.category_field.value,
                "quantity": int(self.quantity_field.value),
                "unit": self.unit_field.value,
                "cost_per_unit": float(self.cost_field.value) if self.cost_field.value else 0.0,
                "min_stock": int(self.min_stock_field.value),
                "expiry_date": expiry_val,
                "sterilization_status": self.sterilization_status_field.value,
                "purpose": self.purpose_field.value if self.category_field.value == "Consumable" else None
            }
            
            if self.item:
                # Handle status change logic for existing items
                new_status = self.sterilization_status_field.value
                current_qty = int(self.quantity_field.value)
                
                # Reset all counts based on the "primary" status selected
                if new_status == "Used":
                    data["quantity"] = 0
                    data["quantity_used"] = current_qty
                    data["quantity_sterilizing"] = 0
                else: # Sterile
                    data["quantity"] = current_qty
                    data["quantity_used"] = 0
                    data["quantity_sterilizing"] = 0

                query = InventoryItem.update(**data).where(InventoryItem.id == self.item.id)
                query.execute()
            else:
                item = InventoryItem.create(**data)
                
                # Create initial Batch
                from database import Batch, ActivityLog
                import datetime
                
                # Use selected purchase date
                purchase_date = self.purchase_date_field.value if self.purchase_date_field.value else datetime.date.today()
                
                # Get details from field
                details_val = self.details_field.value if hasattr(self, 'details_field') else None
                
                Batch.create(
                    item=item,
                    quantity=data["quantity"],
                    expiry_date=expiry_val,
                    purchase_date=purchase_date,
                    cost_per_unit=data["cost_per_unit"],
                    details=details_val
                )

                # Log initial acquisition
                acq_type = self.acquisition_type_field.value
                cost = data["cost_per_unit"] * data["quantity"]
                
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
