import flet as ft
from database import InventoryItem, ActivityLog, Batch
from views.inventory_forms import ItemFormDialog
import datetime

from utils.data_handler import export_to_csv, export_to_pdf, import_from_csv

class InventoryView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.current_tab = "All"
        self.quick_actions_locked = False
        
        # File Pickers
        self.export_csv_dialog = ft.FilePicker(on_result=self.export_csv_result)
        self.export_pdf_dialog = ft.FilePicker(on_result=self.export_pdf_result)
        self.import_csv_dialog = ft.FilePicker(on_result=self.import_csv_result)
        
        self.search_field = ft.TextField(
            hint_text="Search items...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change,
            width=300
        )
        
        self.lock_switch = ft.Switch(
            label="Lock Quick Actions",
            value=False,
            on_change=self.on_lock_change
        )

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="All"),
                ft.Tab(text="Consumable"),
                ft.Tab(text="Instrument"),
                ft.Tab(text="Equipment"),
            ],
        )

        self.controls = [
            # Add FilePickers to the view so they are registered
            self.export_csv_dialog,
            self.export_pdf_dialog,
            self.import_csv_dialog,
            
            ft.Row([
                ft.Text("Inventory", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(text="Export CSV", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self.export_csv_dialog.save_file(allowed_extensions=["csv"], file_name="inventory.csv")),
                            ft.PopupMenuItem(text="Export PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: self.export_pdf_dialog.save_file(allowed_extensions=["pdf"], file_name="inventory.pdf")),
                            ft.PopupMenuItem(text="Import CSV", icon=ft.Icons.UPLOAD, on_click=lambda _: self.import_csv_dialog.pick_files(allowed_extensions=["csv"])),
                        ]
                    ),
                    self.lock_switch,
                    self.search_field,
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_item_click)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.tabs,
            ft.Divider(),
            self.build_data_table()
        ]

    def on_search_change(self, e):
        self.refresh_table()

    def on_tab_change(self, e):
        self.current_tab = e.control.tabs[e.control.selected_index].text
        self.refresh_table()

    def on_lock_change(self, e):
        self.quick_actions_locked = e.control.value
        self.refresh_table()

    def build_data_table(self):
        search_query = self.search_field.value.lower() if hasattr(self, 'search_field') and self.search_field.value else ""
        
        query = InventoryItem.select()
        
        # Filter by Tab
        if self.current_tab != "All":
            query = query.where(InventoryItem.category == self.current_tab)

        # Filter by Search
        if search_query:
            query = query.where(
                (ft.fn.Lower(InventoryItem.name).contains(search_query)) | 
                (ft.fn.Lower(InventoryItem.category).contains(search_query))
            )
        
        items = query
        
        rows = []
        for item in items:
            # Low Stock Logic (Universal for Available/Sterile count)
            is_low_stock = item.quantity < item.min_stock
            
            # Row Color
            row_color = ft.Colors.RED_100 if is_low_stock else None

            # Expiry Logic (Consumables Only)
            is_expired = False
            is_expiring_soon = False
            days_to_expiry = 999
            
            if item.category == "Consumable":
                # Find earliest expiry from batches
                batches = item.batches.where(Batch.quantity > 0).order_by(Batch.expiry_date)
                earliest_batch = batches.first()
                
                if earliest_batch and earliest_batch.expiry_date:
                    today = datetime.date.today()
                    exp_date = earliest_batch.expiry_date
                    if isinstance(exp_date, str):
                        try:
                            exp_date = datetime.datetime.strptime(exp_date, "%Y-%m-%d").date()
                        except:
                            pass
                    
                    if isinstance(exp_date, datetime.date):
                        delta = exp_date - today
                        days_to_expiry = delta.days
                        if days_to_expiry < 0:
                            is_expired = True
                        elif days_to_expiry < 30:
                            is_expiring_soon = True

            expiry_icon = ft.Container()
            if is_expired:
                expiry_icon = ft.Icon(ft.Icons.ACCESS_TIME_FILLED, color=ft.Colors.RED, size=16, tooltip=f"Expired {abs(days_to_expiry)} days ago")
            elif is_expiring_soon:
                expiry_icon = ft.Icon(ft.Icons.ACCESS_TIME_FILLED, color=ft.Colors.ORANGE, size=16, tooltip=f"Expires in {days_to_expiry} days")

            name_content = ft.Row(
                [
                    ft.Text(item.name),
                    expiry_icon
                ]
            )

            rows.append(
                ft.DataRow(
                    color=row_color, # Try passing color directly
                    cells=[
                        ft.DataCell(name_content),
                        ft.DataCell(ft.Text(item.category)),
                        ft.DataCell(
                            ft.Row([
                                # Consumable Status Logic
                                *([
                                    ft.Container(
                                        content=ft.Text("S", color=ft.Colors.WHITE),
                                        bgcolor=ft.Colors.GREEN,
                                        padding=5, border_radius=5, width=25, height=25, alignment=ft.alignment.center,
                                        tooltip="Purpose: Selling"
                                    )
                                ] if item.category == "Consumable" and item.purpose == "Selling" else []),
                                
                                *([
                                    ft.Container(
                                        content=ft.Text("U", color=ft.Colors.WHITE),
                                        bgcolor=ft.Colors.BLUE,
                                        padding=5, border_radius=5, width=25, height=25, alignment=ft.alignment.center,
                                        tooltip="Purpose: Usage"
                                    )
                                ] if item.category == "Consumable" and (item.purpose == "Usage" or item.purpose is None) else []),

                                # Instrument/Equipment Status Logic
                                *([
                                    ft.Container(
                                        content=ft.Text("S", color=ft.Colors.WHITE if item.quantity_used == 0 else ft.Colors.BLACK),
                                        bgcolor=ft.Colors.GREEN if item.quantity_used == 0 else ft.Colors.GREY_300,
                                        padding=5, border_radius=5, width=25, height=25, alignment=ft.alignment.center,
                                        tooltip=f"Available: {item.quantity}"
                                    ),
                                    ft.Container(
                                        content=ft.Text("U", color=ft.Colors.WHITE if item.quantity_used > 0 else ft.Colors.BLACK),
                                        bgcolor=ft.Colors.ORANGE if item.quantity_used > 0 else ft.Colors.GREY_300,
                                        padding=5, border_radius=5, width=25, height=25, alignment=ft.alignment.center,
                                        tooltip=f"Used: {item.quantity_used}"
                                    )
                                ] if item.category != "Consumable" else [])
                            ], spacing=2)
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip="Details & Batches", on_click=lambda e, i=item: self.show_batch_manager(e, i)),
                                ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, tooltip="Quick Deduct", on_click=lambda e, i=item: self.quick_deduct_click(e, i), disabled=self.quick_actions_locked),
                                ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Quick Add", on_click=lambda e, i=item: self.quick_add_click(e, i), disabled=self.quick_actions_locked),
                                *([
                                    ft.IconButton(ft.Icons.SELL, tooltip="Mark Sold", on_click=lambda e, i=item: self.mark_used_click(e, i))
                                ] if item.category == "Consumable" and item.purpose == "Selling" else []),
                                
                                *([
                                    ft.IconButton(ft.Icons.DELETE_SWEEP, tooltip="Mark Consumed", on_click=lambda e, i=item: self.mark_used_click(e, i))
                                ] if item.category == "Consumable" and (item.purpose == "Usage" or item.purpose is None) else []),

                                *([
                                    ft.IconButton(ft.Icons.CLEANING_SERVICES, tooltip="Mark Used", on_click=lambda e, i=item: self.mark_used_click(e, i))
                                ] if item.category != "Consumable" else []),
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda e, i=item: self.edit_item_click(e, i)),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, i=item: self.delete_item_click(e, i))
                            ])
                        ),
                    ],
                )
            )

        return ft.Column(
            [
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Name")),
                        ft.DataColumn(ft.Text("Category")),
                        ft.DataColumn(ft.Text("Status")),
                        ft.DataColumn(ft.Text("Actions")),
                    ],
                    rows=rows,
                    width=float('inf'), # Expand to fill
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def delete_item_click(self, e, item):
        # Direct Delete Confirmation
        def confirm_delete(e):
            # Delete all batches first
            for batch in item.batches:
                batch.delete_instance()
            item.delete_instance()
            
            e.page.close(dialog)
            self.refresh_table()
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted item: {item.name}"))
            e.page.snack_bar.open = True
            e.page.update()

        def cancel_delete(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete {item.name}? This will delete all associated batches."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def quick_deduct_click(self, e, item):
        if item.quantity > 0:
            # FIFO Deduction from Batches for ALL categories
            amount_to_deduct = 1
            batches = item.batches.order_by(Batch.expiry_date, Batch.added_date)
            
            remaining = amount_to_deduct
            for batch in batches:
                if batch.quantity > 0:
                    deduct = min(remaining, batch.quantity)
                    batch.quantity -= deduct
                    batch.save()
                    remaining -= deduct
                    if remaining == 0:
                        break
            
            # Update total quantity
            item.quantity -= amount_to_deduct
            item.save()
            cost = item.cost_per_unit # Fallback or average? Ideally should track cost from specific batch but for single unit quick deduct, item cost is approx.
            
            action_type = "Usage"
            details = f"Used 1 {item.unit} of {item.name}"
            
            if item.category == "Consumable":
                if item.purpose == "Selling":
                    action_type = "Sale"
                    details = f"Sold 1 {item.unit} of {item.name}"
                else:
                    action_type = "Usage"
                    details = f"Consumed 1 {item.unit} of {item.name}"
            
            ActivityLog.create(action=action_type, details=details, cost=cost)

            self.refresh_table()
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deducted 1 {item.unit} of {item.name}"))
            e.page.snack_bar.open = True
            e.page.update()

    def add_item_click(self, e):
        dialog = ItemFormDialog(e.page, self.refresh_table)
        e.page.open(dialog)

    def quick_add_click(self, e, item):
        # Universal "Add Batch" dialog for all categories
        expiry_field = ft.TextField(label="Expiry Date (YYYY-MM-DD)", hint_text="YYYY-MM-DD", visible=(item.category == "Consumable"), read_only=True)
        purchase_date_field = ft.TextField(label="Purchase Date (YYYY-MM-DD)", value=datetime.date.today().strftime("%Y-%m-%d"), read_only=True)
        cost_field = ft.TextField(label="Cost per Unit (PKR)", value=str(item.cost_per_unit), keyboard_type=ft.KeyboardType.NUMBER)
        details_field = ft.TextField(label="Batch Details (Company, Grade, etc.)", multiline=True)
        qty_field = ft.TextField(label="Quantity", value="1", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        def set_date(field, date_val):
            if date_val:
                field.value = date_val.strftime("%Y-%m-%d")
                field.update()

        def pick_expiry_date(e):
            e.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime(2020, 1, 1),
                    last_date=datetime.datetime(2030, 12, 31),
                    on_change=lambda e: set_date(expiry_field, e.control.value)
                )
            )

        def pick_purchase_date(e):
            e.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime(2020, 1, 1),
                    last_date=datetime.datetime(2030, 12, 31),
                    on_change=lambda e: set_date(purchase_date_field, e.control.value)
                )
            )
        
        def confirm_add(e):
            try:
                qty = int(qty_field.value)
                cost = float(cost_field.value)
                details = details_field.value
                
                expiry_val = None
                if item.category == "Consumable" and expiry_field.value:
                    expiry_val = expiry_field.value
                
                purchase_val = purchase_date_field.value if purchase_date_field.value else datetime.date.today()

                # Create new batch
                Batch.create(
                    item=item,
                    quantity=qty,
                    expiry_date=expiry_val,
                    purchase_date=purchase_val,
                    cost_per_unit=cost,
                    details=details
                )
                
                # Update item total quantity
                item.quantity += qty
                item.cost_per_unit = cost # Update latest cost
                item.save()
                
                # Log activity
                ActivityLog.create(
                    action="Stock Added",
                    details=f"Added {qty} {item.unit} of {item.name} (Batch Add)",
                    cost=cost * qty
                )
                
                add_dialog.open = False
                e.page.update()
                self.refresh_table()
                
            except ValueError:
                pass # Handle validation error

        add_dialog = ft.AlertDialog(
            title=ft.Text("Add Stock (New Batch)"),
            content=ft.Column([
                ft.Text(f"Adding to {item.name}"),
                qty_field,
                cost_field,
                ft.Row([
                    purchase_date_field,
                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_purchase_date)
                ]),
                ft.Row([
                    expiry_field,
                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_expiry_date, visible=(item.category == "Consumable"))
                ]),
                details_field
            ], tight=True, width=400),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: e.page.close(add_dialog)),
                ft.TextButton("Confirm", on_click=confirm_add),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(add_dialog)

    def edit_item_click(self, e, item):
        from views.inventory_forms import ItemFormDialog
        from views.batch_forms import BatchFormDialog

        def open_item_edit(e):
            e.page.close(selection_dialog)
            dialog = ItemFormDialog(e.page, self.refresh_table, item)
            e.page.open(dialog)

        def open_batch_edit(e, batch):
            e.page.close(selection_dialog)
            dialog = BatchFormDialog(e.page, self.refresh_table, batch)
            e.page.open(dialog)

        # Create list of batches for selection
        batch_rows = []
        for b in item.batches.order_by(Batch.added_date.desc()):
            batch_rows.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.INVENTORY_2),
                    title=ft.Text(f"Batch #{b.id}"),
                    subtitle=ft.Text(f"Qty: {b.quantity} | Exp: {b.expiry_date}"),
                    on_click=lambda e, b=b: open_batch_edit(e, b)
                )
            )

        selection_content = ft.Column([
            ft.ElevatedButton("Edit Main Item Settings (Name, Category)", on_click=open_item_edit, width=400),
            ft.Divider(),
            ft.Text("Or Select a Batch to Edit:", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.ListView(controls=batch_rows, height=200),
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            )
        ], tight=True, width=400)

        selection_dialog = ft.AlertDialog(
            title=ft.Text(f"Edit {item.name}"),
            content=selection_content,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: e.page.close(selection_dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(selection_dialog)

    def delete_item_click(self, e, item):
        # Split Delete Dialog: List of Batches vs Entire Item
        
        def delete_batch(e, batch):
            # Confirm Batch Delete
            def confirm_batch_del(e):
                item.quantity -= batch.quantity
                batch.delete_instance()
                item.save()
                
                e.page.close(confirm_dialog)
                e.page.close(main_dialog)
                self.refresh_table()
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted Batch #{batch.id}"))
                e.page.snack_bar.open = True
                e.page.update()

            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Confirm Batch Delete"),
                content=ft.Text(f"Delete Batch #{batch.id} (Qty: {batch.quantity})?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: e.page.close(confirm_dialog)),
                    ft.TextButton("Delete", on_click=confirm_batch_del, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            e.page.open(confirm_dialog)

        def confirm_item_delete(e):
            # Delete all batches first
            for batch in item.batches:
                batch.delete_instance()
            item.delete_instance()
            
            e.page.close(main_dialog)
            self.refresh_table()
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted item: {item.name}"))
            e.page.snack_bar.open = True
            e.page.update()

        # Create list of batches
        batch_rows = []
        batches = list(item.batches.order_by(Batch.added_date.desc()))
        
        if not batches:
            batch_rows.append(ft.Text("No batches found.", italic=True))
        else:
            for b in batches:
                batch_rows.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INVENTORY_2, size=20),
                        title=ft.Text(f"Batch #{b.id}"),
                        subtitle=ft.Text(f"Qty: {b.quantity} | Exp: {b.expiry_date or 'N/A'}"),
                        trailing=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, 
                            icon_color=ft.Colors.RED_400,
                            tooltip="Delete this batch",
                            on_click=lambda e, b=b: delete_batch(e, b)
                        ),
                        dense=True
                    )
                )

        main_dialog = ft.AlertDialog(
            title=ft.Text(f"Delete Options: {item.name}"),
            content=ft.Column([
                ft.Text("Option 1: Delete Specific Batch", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.ListView(controls=batch_rows, height=200, spacing=5),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    padding=5
                ),
                ft.Divider(),
                ft.Text("Option 2: Delete Entire Item", weight=ft.FontWeight.BOLD),
                ft.Text("Warning: This will delete the item and ALL its batches.", size=12, color=ft.Colors.GREY),
                ft.ElevatedButton("Delete Entire Item", on_click=confirm_item_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, width=400),
            ], tight=True, width=400),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: e.page.close(main_dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(main_dialog)

    def show_batch_manager(self, e, item):
        def close_dialog(e):
            e.page.close(dialog)
            self.refresh_table()

        def delete_batch(e, batch):
            def confirm_batch_delete(e):
                try:
                    qty_to_remove = int(qty_field.value)
                    if qty_to_remove <= 0:
                        return
                    
                    if qty_to_remove >= batch.quantity:
                        # Remove entire batch
                        item.quantity -= batch.quantity
                        batch.delete_instance()
                    else:
                        # Partial removal
                        batch.quantity -= qty_to_remove
                        batch.save()
                        item.quantity -= qty_to_remove
                    
                    item.save()
                    delete_dialog.open = False
                    e.page.update()
                    refresh_batch_list()
                    self.refresh_table()
                    
                except ValueError:
                    pass

            qty_field = ft.TextField(label="Quantity to remove", value=str(batch.quantity), keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
            
            delete_dialog = ft.AlertDialog(
                title=ft.Text("Remove from Batch"),
                content=ft.Column([
                    ft.Text(f"Batch Qty: {batch.quantity}"),
                    qty_field
                ], tight=True),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: e.page.close(delete_dialog)),
                    ft.TextButton("Remove", on_click=confirm_batch_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            e.page.open(delete_dialog)
            
        def refresh_batch_list(update=True):
            batches = item.batches.order_by(Batch.added_date.desc())
            
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Qty"), numeric=True),
                ft.DataColumn(ft.Text("Cost"), numeric=True),
                ft.DataColumn(ft.Text("Purchase Date")),
                ft.DataColumn(ft.Text("Expiry")),
                ft.DataColumn(ft.Text("Details")),
            ]
            
            rows = []
            for b in batches:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(b.id))),
                    ft.DataCell(ft.Text(str(b.quantity))),
                    ft.DataCell(ft.Text(str(b.cost_per_unit))),
                    ft.DataCell(ft.Text(str(b.purchase_date) if b.purchase_date else "-")),
                    ft.DataCell(ft.Text(str(b.expiry_date) if b.expiry_date else "-")),
                    ft.DataCell(ft.Text(b.details or "-")),
                ]))
            
            batch_table = ft.DataTable(
                columns=columns, 
                rows=rows, 
                column_spacing=20,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_200),
                horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_200),
                heading_row_color=ft.Colors.BLUE_GREY_50,
                heading_row_height=40,
                data_row_max_height=40
            )
            
            batch_list.content = ft.Column([batch_table], scroll=ft.ScrollMode.AUTO, height=300)
            
            if update:
                batch_list.update()

        batch_list = ft.Container() # Container to hold the table
        refresh_batch_list(update=False)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Batch Details: {item.name}"),
            content=ft.Column([
                batch_list
            ], width=600, height=400),
            actions=[
                ft.TextButton("Close", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def mark_used_click(self, e, item):
        # Determine context
        action_title = "Mark Used"
        amount_label = "Amount Used"
        
        if item.category == "Consumable":
            if item.purpose == "Selling":
                action_title = "Confirm Sale"
                amount_label = "Amount Sold"
            else:
                action_title = "Confirm Consumption"
                amount_label = "Amount Consumed"

        amount_field = ft.TextField(label=amount_label, value="1", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        def confirm_used(e):
            print("Confirm Used clicked")
            try:
                if not amount_field.value:
                     e.page.snack_bar = ft.SnackBar(ft.Text("Please enter an amount"))
                     e.page.snack_bar.open = True
                     e.page.update()
                     return

                amount = int(amount_field.value)
                if amount > item.quantity:
                    e.page.snack_bar = ft.SnackBar(ft.Text(f"Error: Only {item.quantity} available"))
                    e.page.snack_bar.open = True
                    e.page.update()
                    return
                
                if amount <= 0:
                    e.page.snack_bar = ft.SnackBar(ft.Text("Error: Amount must be positive"))
                    e.page.snack_bar.open = True
                    e.page.update()
                    return

                # FIFO Deduction from Batches for ALL categories
                remaining = amount
                batches = item.batches.order_by(Batch.expiry_date, Batch.added_date)
                
                total_cost = 0.0
                
                for batch in batches:
                    if batch.quantity > 0:
                        deduct = min(remaining, batch.quantity)
                        batch.quantity -= deduct
                        batch.save()
                        
                        # Calculate cost for this specific batch chunk
                        total_cost += deduct * batch.cost_per_unit
                        
                        remaining -= deduct
                        if remaining == 0:
                            break
                
                item.quantity -= amount
                
                if item.category == "Consumable":
                    # Consumables are consumed (gone forever)
                    item.save()
                    
                    action_type = "Usage"
                    details = f"Consumed {amount} {item.unit} of {item.name}"
                    
                    if item.purpose == "Selling":
                        action_type = "Sale"
                        details = f"Sold {amount} {item.unit} of {item.name}"
                    
                    ActivityLog.create(action=action_type, details=details, cost=total_cost)
                    # Cost is fully calculated
                else:
                    # Instruments/Equipment go to sterilization cycle
                    item.quantity_used += amount
                    item.save()
                    total_cost = 0.0 # No financial cost for using reusable items
                    details = f"Marked {amount} {item.unit} of {item.name} as Used"
                    ActivityLog.create(action="Usage", details=details, cost=total_cost)
                
                self.refresh_table()
                e.page.close(dialog)
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Processed {amount} {item.name}"))
                e.page.snack_bar.open = True
                e.page.update()
                print(f"Successfully processed {amount}")
            except ValueError:
                e.page.snack_bar = ft.SnackBar(ft.Text("Error: Invalid amount"))
                e.page.snack_bar.open = True
                e.page.update()
            except Exception as ex:
                print(f"Error in confirm_used: {ex}")
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
                e.page.snack_bar.open = True
                e.page.update()

        def cancel_used(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text(action_title),
            content=ft.Column([
                ft.Text(f"Quantity to process for {item.name}:"),
                amount_field
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_used),
                ft.ElevatedButton("Confirm", on_click=confirm_used)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def refresh_table(self):
        self.controls[-1] = self.build_data_table()
        self.update()

    def export_csv_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = InventoryItem.select()
            fields = ["name", "category", "quantity", "unit", "min_stock", "cost_per_unit", "purpose"]
            success, msg = export_to_csv(query, e.path, fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def export_pdf_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = InventoryItem.select()
            fields = ["name", "category", "quantity", "unit", "min_stock"]
            success, msg = export_to_pdf(query, e.path, "Inventory Report", fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def import_csv_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            field_map = {
                "name": "name",
                "category": "category",
                "quantity": "quantity",
                "unit": "unit",
                "min_stock": "min_stock",
                "cost_per_unit": "cost_per_unit",
                "purpose": "purpose"
            }
            success, msg = import_from_csv(InventoryItem, e.files[0].path, field_map)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()
            self.refresh_table()
