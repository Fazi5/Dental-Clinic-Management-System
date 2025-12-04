import flet as ft
from database import InventoryItem, ActivityLog

from utils.data_handler import export_to_csv, export_to_pdf

class SterilizationView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.export_csv_dialog = ft.FilePicker(on_result=self.export_csv_result)
        self.export_pdf_dialog = ft.FilePicker(on_result=self.export_pdf_result)

        self.controls = [
            self.export_csv_dialog,
            self.export_pdf_dialog,
            
            ft.Row([
                ft.Text("Sterilization Tracking", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(text="Export CSV", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self.export_csv_dialog.save_file(allowed_extensions=["csv"], file_name="sterilization_needed.csv")),
                            ft.PopupMenuItem(text="Export PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: self.export_pdf_dialog.save_file(allowed_extensions=["pdf"], file_name="sterilization_needed.pdf")),
                        ]
                    ),
                    ft.ElevatedButton("Sterilize All Instruments", on_click=self.sterilize_all_instruments, icon=ft.Icons.CLEANING_SERVICES),
                    ft.ElevatedButton("Sterilize All Equipment", on_click=self.sterilize_all_equipment, icon=ft.Icons.CLEANING_SERVICES),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text("Items requiring sterilization or currently in autoclave.", italic=True),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_data_table(self):
        # Filter for items that have used quantities
        items = InventoryItem.select().where(InventoryItem.quantity_used > 0)
        
        if items.count() == 0:
            return ft.Text("No items currently require sterilization.", color=ft.Colors.GREEN)

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Used Qty")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(item.category)),
                        ft.DataCell(ft.Text(str(item.quantity_used), color=ft.Colors.ORANGE if item.quantity_used > 0 else None)),
                        ft.DataCell(
                            ft.ElevatedButton("Mark Sterile", on_click=lambda e, i=item: self.mark_sterile(e, i))
                        ),
                    ]
                ) for item in items
            ],
            width=float('inf'),
        )

    def sterilize_all_instruments(self, e):
        self.bulk_sterilize("Instrument")

    def sterilize_all_equipment(self, e):
        self.bulk_sterilize("Equipment")

    def bulk_sterilize(self, category):
        items = InventoryItem.select().where((InventoryItem.category == category) & (InventoryItem.quantity_used > 0))
        count = items.count()
        if count == 0:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"No {category}s to sterilize"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        total_qty = 0
        for item in items:
            qty = item.quantity_used
            item.quantity += qty
            item.quantity_used = 0
            item.save()
            total_qty += qty
        
        ActivityLog.create(action="Sterilization", details=f"Bulk Sterilized {total_qty} {category}s", cost=0.0)
        
        self.refresh_table()
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Sterilized all {category}s ({total_qty} items)"))
        self.page.snack_bar.open = True
        self.page.update()

    def mark_sterile(self, e, item):
        self.show_quantity_dialog(e, item, item.quantity_used)

    def show_quantity_dialog(self, e, item, max_qty):
        amount_field = ft.TextField(label="Quantity", value=str(max_qty), keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        def confirm_move(e):
            try:
                if not amount_field.value:
                     e.page.snack_bar = ft.SnackBar(ft.Text("Please enter an amount"))
                     e.page.snack_bar.open = True
                     e.page.update()
                     return

                amount = int(amount_field.value)
                if amount > max_qty:
                    e.page.snack_bar = ft.SnackBar(ft.Text(f"Error: Only {max_qty} available"))
                    e.page.snack_bar.open = True
                    e.page.update()
                    return
                
                if amount <= 0:
                    e.page.snack_bar = ft.SnackBar(ft.Text("Error: Amount must be positive"))
                    e.page.snack_bar.open = True
                    e.page.update()
                    return

                # Move from Used directly to Sterile (Quantity)
                item.quantity_used -= amount
                item.quantity += amount
                msg = f"Restocked {amount} {item.name} as Sterile"

                item.save()
                
                # Log activity
                ActivityLog.create(action="Sterilization", details=msg, cost=0.0)

                self.refresh_table()
                e.page.close(dialog)
                e.page.snack_bar = ft.SnackBar(ft.Text(msg))
                e.page.snack_bar.open = True
                e.page.update()
            except ValueError:
                e.page.snack_bar = ft.SnackBar(ft.Text("Error: Invalid amount"))
                e.page.snack_bar.open = True
                e.page.update()

        def cancel_move(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Mark as Sterile"),
            content=ft.Column([
                ft.Text(f"How many {item.name} to mark sterile? (Max: {max_qty})"),
                amount_field
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_move),
                ft.ElevatedButton("Confirm", on_click=confirm_move)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def refresh_table(self):
        self.controls[-1] = self.build_data_table()
        self.update()

    def export_csv_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = InventoryItem.select().where(InventoryItem.quantity_used > 0)
            fields = ["name", "category", "quantity_used"]
            success, msg = export_to_csv(query, e.path, fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def export_pdf_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = InventoryItem.select().where(InventoryItem.quantity_used > 0)
            fields = ["name", "category", "quantity_used"]
            success, msg = export_to_pdf(query, e.path, "Sterilization Needed Report", fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()
