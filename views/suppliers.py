import flet as ft
from database import Supplier

class SupplierFormDialog(ft.AlertDialog):
    def __init__(self, page, on_success, supplier=None):
        super().__init__()
        self.page = page
        self.on_success = on_success
        self.supplier = supplier
        self.title = ft.Text("Add Supplier" if not supplier else "Edit Supplier")
        
        self.name_field = ft.TextField(label="Name", value=supplier.name if supplier else "")
        self.email_field = ft.TextField(label="Email", value=supplier.email if supplier else "")
        self.phone_field = ft.TextField(label="Phone", value=supplier.phone if supplier else "")
        self.location_field = ft.TextField(label="Location", value=supplier.location if supplier else "")
        self.contact_info_field = ft.TextField(label="Other Contact Info", value=supplier.contact_info if supplier else "", multiline=True)
        
        self.content = ft.Column(
            [
                self.name_field,
                self.email_field,
                self.phone_field,
                self.location_field,
                self.contact_info_field,
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
                "name": self.name_field.value,
                "email": self.email_field.value,
                "phone": self.phone_field.value,
                "location": self.location_field.value,
                "contact_info": self.contact_info_field.value,
            }
            
            if self.supplier:
                query = Supplier.update(**data).where(Supplier.id == self.supplier.id)
                query.execute()
            else:
                Supplier.create(**data)
            
            self.close(None)
            self.on_success()
            
        except Exception as ex:
            print(f"Error saving supplier: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

class SupplierView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.controls = [
            ft.Row([
                ft.Text("Suppliers", size=30, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.ADD, on_click=self.add_supplier_click)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_data_table(self):
        suppliers = Supplier.select()
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Phone")),
                ft.DataColumn(ft.Text("Location")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(s.name)),
                        ft.DataCell(ft.Text(s.email or "-")),
                        ft.DataCell(ft.Text(s.phone or "-")),
                        ft.DataCell(ft.Text(s.location or "-")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda e, s=s: self.edit_supplier_click(e, s)),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, s=s: self.delete_supplier_click(e, s))
                            ])
                        ),
                    ]
                ) for s in suppliers
            ],
            width=float('inf'),
        )

    def add_supplier_click(self, e):
        dialog = SupplierFormDialog(e.page, self.refresh_table)
        e.page.open(dialog)

    def edit_supplier_click(self, e, supplier):
        dialog = SupplierFormDialog(e.page, self.refresh_table, supplier)
        e.page.open(dialog)

    def delete_supplier_click(self, e, supplier):
        def confirm_delete(e):
            supplier.delete_instance()
            self.refresh_table()
            e.page.close(dialog)
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted supplier: {supplier.name}"))
            e.page.snack_bar.open = True
            e.page.update()

        def cancel_delete(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete {supplier.name}?"),
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
