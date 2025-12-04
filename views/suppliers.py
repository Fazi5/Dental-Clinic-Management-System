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
        self.category_field = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Dental Supplies"),
                ft.dropdown.Option("Dental Laboratory"),
            ],
            value=supplier.category if supplier else "Dental Supplies"
        )
        self.email_field = ft.TextField(label="Email", value=supplier.email if supplier else "")
        self.phone_field = ft.TextField(label="Phone", value=supplier.phone if supplier else "")
        self.location_field = ft.TextField(label="Location", value=supplier.location if supplier else "")
        self.contact_info_field = ft.TextField(label="WhatsApp Number", value=supplier.contact_info if supplier else "")
        self.details_field = ft.TextField(label="Additional Details", value=supplier.details if supplier else "", multiline=True, min_lines=3)
        
        self.content = ft.Column(
            [
                self.name_field,
                self.category_field,
                self.email_field,
                self.phone_field,
                self.location_field,
                self.contact_info_field,
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

    def close(self, e):
        self.page.close(self)

    def save(self, e):
        try:
            name = self.name_field.value
            category = self.category_field.value
            email = self.email_field.value
            phone = self.phone_field.value
            location = self.location_field.value
            whatsapp = self.contact_info_field.value
            details = self.details_field.value

            # Validation
            if not name or not phone or not location:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error: Name, Phone, and Location are required."))
                self.page.snack_bar.open = True
                self.page.update()
                return

            if email and "@" not in email:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error: Invalid email format."))
                self.page.snack_bar.open = True
                self.page.update()
                return

            data = {
                "name": name,
                "category": category,
                "email": email,
                "phone": phone,
                "location": location,
                "contact_info": whatsapp,
                "details": details,
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

from utils.data_handler import export_to_csv, export_to_pdf, import_from_csv

class SupplierView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.export_csv_dialog = ft.FilePicker(on_result=self.export_csv_result)
        self.export_pdf_dialog = ft.FilePicker(on_result=self.export_pdf_result)
        self.import_csv_dialog = ft.FilePicker(on_result=self.import_csv_result)

        self.controls = [
            self.export_csv_dialog,
            self.export_pdf_dialog,
            self.import_csv_dialog,
            
            ft.Row([
                ft.Text("Suppliers", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(text="Export CSV", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self.export_csv_dialog.save_file(allowed_extensions=["csv"], file_name="suppliers.csv")),
                            ft.PopupMenuItem(text="Export PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: self.export_pdf_dialog.save_file(allowed_extensions=["pdf"], file_name="suppliers.pdf")),
                            ft.PopupMenuItem(text="Import CSV", icon=ft.Icons.UPLOAD, on_click=lambda _: self.import_csv_dialog.pick_files(allowed_extensions=["csv"])),
                        ]
                    ),
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_supplier_click)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_data_table(self):
        suppliers = Supplier.select()
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(s.name)),
                        ft.DataCell(ft.Text(s.category or "-")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip="Details", on_click=lambda e, s=s: self.show_details_click(e, s)),
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda e, s=s: self.edit_supplier_click(e, s)),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, s=s: self.delete_supplier_click(e, s))
                            ])
                        ),
                    ]
                ) for s in suppliers
            ],
            width=float('inf'),
        )

    def show_details_click(self, e, supplier):
        content = ft.Column([
            ft.Text(f"Name: {supplier.name}", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Category: {supplier.category or 'N/A'}"),
            ft.Text(f"Email: {supplier.email or 'N/A'}"),
            ft.Text(f"Phone: {supplier.phone or 'N/A'}"),
            ft.Text(f"Location: {supplier.location or 'N/A'}"),
            ft.Text(f"WhatsApp: {supplier.contact_info or 'N/A'}"),
            ft.Text(f"Details: {supplier.details or 'N/A'}"),
        ], tight=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Supplier Details"),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda e: e.page.close(dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

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

    def export_csv_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = Supplier.select()
            fields = ["name", "category", "email", "phone", "location", "contact_info", "details"]
            success, msg = export_to_csv(query, e.path, fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def export_pdf_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = Supplier.select()
            fields = ["name", "category", "email", "phone", "location"]
            success, msg = export_to_pdf(query, e.path, "Supplier Report", fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def import_csv_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            field_map = {
                "name": "name",
                "category": "category",
                "email": "email",
                "phone": "phone",
                "location": "location",
                "contact_info": "contact_info",
                "details": "details"
            }
            success, msg = import_from_csv(Supplier, e.files[0].path, field_map)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()
            self.refresh_table()
