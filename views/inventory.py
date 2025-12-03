import flet as ft
from database import InventoryItem, ActivityLog
from views.inventory_forms import ItemFormDialog
import datetime

class InventoryView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.search_field = ft.TextField(
            hint_text="Search items...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change,
            width=300
        )
        self.controls = [
            ft.Row([
                ft.Text("Inventory", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.search_field,
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_item_click)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_data_table()
        ]

    def on_search_change(self, e):
        self.refresh_table()

    def build_data_table(self):
        search_query = self.search_field.value.lower() if hasattr(self, 'search_field') and self.search_field.value else ""
        
        if search_query:
            items = InventoryItem.select().where(
                (ft.fn.Lower(InventoryItem.name).contains(search_query)) | 
                (ft.fn.Lower(InventoryItem.category).contains(search_query))
            )
        else:
            items = InventoryItem.select()
        
        rows = []
        for item in items:
            is_low_stock = item.quantity < item.min_stock
            
            # Expiry Logic
            is_expired = False
            days_to_expiry = 999
            if item.expiry_date:
                today = datetime.date.today()
                # Handle string date if it comes back as string from sqlite/peewee sometimes
                exp_date = item.expiry_date
                if isinstance(exp_date, str):
                    try:
                        exp_date = datetime.datetime.strptime(exp_date, "%Y-%m-%d").date()
                    except:
                        pass # Keep as is or ignore
                
                if isinstance(exp_date, datetime.date):
                    delta = exp_date - today
                    days_to_expiry = delta.days
                    if days_to_expiry < 30: # Alert if expiring in 30 days
                        is_expired = True

            qty_content = ft.Row(
                [
                    ft.Text(str(item.quantity), color=ft.Colors.RED if is_low_stock else None, weight=ft.FontWeight.BOLD if is_low_stock else None),
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED, size=16) if is_low_stock else ft.Container()
                ],
                alignment=ft.MainAxisAlignment.END, # Align numeric value to right/end to match column header
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            
            name_content = ft.Row(
                [
                    ft.Text(item.name),
                    ft.Icon(ft.Icons.ACCESS_TIME_FILLED, color=ft.Colors.ORANGE, size=16, tooltip=f"Expires in {days_to_expiry} days") if is_expired else ft.Container()
                ]
            )

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(name_content),
                        ft.DataCell(ft.Text(item.category)),
                        ft.DataCell(qty_content),
                        ft.DataCell(ft.Text(item.unit)),
                        ft.DataCell(ft.Text(item.sterilization_status or "-")),
                        ft.DataCell(
                            ft.Row([
                            ft.Row([
                                ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, tooltip="Quick Deduct", on_click=lambda e, i=item: self.quick_deduct_click(e, i)),
                                ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Quick Add", on_click=lambda e, i=item: self.quick_add_click(e, i)),
                                ft.IconButton(ft.Icons.CLEANING_SERVICES, tooltip="Mark Used", on_click=lambda e, i=item: self.mark_used_click(e, i)),
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda e, i=item: self.edit_item_click(e, i)),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, i=item: self.delete_item_click(e, i))
                            ])
                        ),
                    ],
                )
            )

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Qty"), numeric=True),
                ft.DataColumn(ft.Text("Unit")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            width=float('inf'), # Expand to fill
        )

    def quick_deduct_click(self, e, item):
        if item.quantity > 0:
            item.quantity -= 1
            item.save()
            cost = item.cost_per_unit
            ActivityLog.create(action="Usage", details=f"Used 1 {item.unit} of {item.name}", cost=cost)
            self.refresh_table()
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deducted 1 {item.unit} of {item.name}"))
            e.page.snack_bar.open = True
            e.page.update()

    def add_item_click(self, e):
        dialog = ItemFormDialog(e.page, self.refresh_table)
        e.page.open(dialog)

    def quick_add_click(self, e, item):
        item.quantity += 1
        item.save()
        cost = item.cost_per_unit
        ActivityLog.create(action="Restock", details=f"Added 1 {item.unit} of {item.name}", cost=cost)
        self.refresh_table()
        e.page.snack_bar = ft.SnackBar(ft.Text(f"Added 1 {item.unit} of {item.name}"))
        e.page.snack_bar.open = True
        e.page.update()

    def edit_item_click(self, e, item):
        dialog = ItemFormDialog(e.page, self.refresh_table, item)
        e.page.open(dialog)

    def delete_item_click(self, e, item):
        def confirm_delete(e):
            item.delete_instance()
            self.refresh_table()
            e.page.close(dialog)
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted item: {item.name}"))
            e.page.snack_bar.open = True
            e.page.update()

        def cancel_delete(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete {item.name}?"),
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
