import flet as ft
from database import InventoryItem

class SterilizationView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.controls = [
            ft.Text("Sterilization Tracking", size=30, weight=ft.FontWeight.BOLD),
            ft.Text("Items requiring sterilization or currently in autoclave.", italic=True),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_data_table(self):
        # Filter for items that have used or sterilizing quantities
        items = InventoryItem.select().where((InventoryItem.quantity_used > 0) | (InventoryItem.quantity_sterilizing > 0))
        
        if items.count() == 0:
            return ft.Text("No items currently require sterilization.", color=ft.Colors.GREEN)

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Used Qty")),
                ft.DataColumn(ft.Text("In-Autoclave Qty")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(str(item.quantity_used), color=ft.Colors.ORANGE if item.quantity_used > 0 else None)),
                        ft.DataCell(ft.Text(str(item.quantity_sterilizing), color=ft.Colors.BLUE if item.quantity_sterilizing > 0 else None)),
                        ft.DataCell(
                            ft.Row([
                                ft.ElevatedButton("To Autoclave", on_click=lambda e, i=item: self.move_to_autoclave(e, i), visible=item.quantity_used > 0),
                                ft.ElevatedButton("To Sterile", on_click=lambda e, i=item: self.move_to_sterile(e, i), visible=item.quantity_sterilizing > 0),
                            ])
                        ),
                    ]
                ) for item in items
            ],
            width=float('inf'),
        )

    def move_to_autoclave(self, e, item):
        # Move all used to sterilizing
        amount = item.quantity_used
        item.quantity_used = 0
        item.quantity_sterilizing += amount
        item.save()
        self.refresh_table()
        e.page.snack_bar = ft.SnackBar(ft.Text(f"Moved {amount} {item.name} to Autoclave"))
        e.page.snack_bar.open = True
        e.page.update()

    def move_to_sterile(self, e, item):
        # Move all sterilizing back to main quantity (sterile)
        amount = item.quantity_sterilizing
        item.quantity_sterilizing = 0
        item.quantity += amount
        item.save()
        self.refresh_table()
        e.page.snack_bar = ft.SnackBar(ft.Text(f"Restocked {amount} {item.name} as Sterile"))
        e.page.snack_bar.open = True
        e.page.update()

    def refresh_table(self):
        self.controls[-1] = self.build_data_table()
        self.update()
