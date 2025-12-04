import flet as ft
import datetime
from database import LabCase, Supplier

class LabCaseFormDialog(ft.AlertDialog):
    def __init__(self, page, on_success, case=None):
        super().__init__()
        self.page = page
        self.on_success = on_success
        self.case = case
        self.title = ft.Text("Add Lab Case" if not case else "Edit Lab Case")
        
        # Form Fields
        self.patient_name_field = ft.TextField(label="Patient Name", value=case.patient_name if case else "")
        
        # Lab Dropdown (Filter for Dental Laboratory)
        labs = Supplier.select().where(Supplier.category == "Dental Laboratory")
        lab_options = [ft.dropdown.Option(text=l.name, key=str(l.id)) for l in labs]
        self.lab_field = ft.Dropdown(
            label="Lab", 
            options=lab_options, 
            value=str(case.lab.id) if case and case.lab else None
        )
        
        self.work_type_field = ft.Dropdown(
            label="Work Type",
            options=[
                ft.dropdown.Option("Crown"),
                ft.dropdown.Option("Bridge"),
                ft.dropdown.Option("Denture"),
                ft.dropdown.Option("Implant"),
                ft.dropdown.Option("Orthodontic Appliance"),
                ft.dropdown.Option("Other"),
            ],
            value=case.work_type if case else "Crown"
        )
        
        self.sent_date_field = ft.TextField(label="Sent Date", value=str(case.sent_date) if case else str(datetime.date.today()), read_only=True)
        self.due_date_field = ft.TextField(label="Due Date", value=str(case.due_date) if case and case.due_date else "", read_only=True)
        self.notes_field = ft.TextField(label="Notes", value=case.notes if case else "", multiline=True)

        # Date Pickers
        def pick_sent_date(e):
            self.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime(2023, 1, 1),
                    last_date=datetime.datetime(2030, 12, 31),
                    on_change=lambda e: setattr(self.sent_date_field, 'value', str(e.control.value.date())) or self.page.update()
                )
            )

        def pick_due_date(e):
            self.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime(2023, 1, 1),
                    last_date=datetime.datetime(2030, 12, 31),
                    on_change=lambda e: setattr(self.due_date_field, 'value', str(e.control.value.date())) or self.page.update()
                )
            )

        self.content = ft.Column(
            [
                self.patient_name_field,
                self.lab_field,
                self.work_type_field,
                ft.Row([
                    self.sent_date_field,
                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_sent_date)
                ]),
                ft.Row([
                    self.due_date_field,
                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=pick_due_date)
                ]),
                self.notes_field
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
            # Validation Logic
            required_fields = {
                "Patient Name": self.patient_name_field.value,
                "Lab": self.lab_field.value,
                "Work Type": self.work_type_field.value,
                "Sent Date": self.sent_date_field.value,
                "Due Date": self.due_date_field.value
            }

            # Check for empty values
            missing_fields = [name for name, value in required_fields.items() if not value or str(value).strip() == ""]
            
            if missing_fields:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Please fill in: {', '.join(missing_fields)}"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            data = {
                "patient_name": self.patient_name_field.value,
                "lab_id": int(self.lab_field.value),
                "work_type": self.work_type_field.value,
                "sent_date": self.sent_date_field.value,
                "due_date": self.due_date_field.value if self.due_date_field.value else None,
                "notes": self.notes_field.value
            }
            
            from database import ActivityLog
            if self.case:
                query = LabCase.update(**data).where(LabCase.id == self.case.id)
                query.execute()
                ActivityLog.create(action="Labworks", details=f"Updated Lab Case for {self.patient_name_field.value}", cost=0.0)
            else:
                LabCase.create(**data)
                ActivityLog.create(action="Labworks", details=f"Sent {self.work_type_field.value} for {self.patient_name_field.value} to Lab", cost=0.0)
            
            self.close(None)
            self.on_success()
            
        except Exception as ex:
            print(f"Error saving lab case: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

from utils.data_handler import export_to_csv, export_to_pdf, import_from_csv

class LabworksView(ft.Column):
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
                ft.Text("Labworks Management", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(text="Export CSV", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self.export_csv_dialog.save_file(allowed_extensions=["csv"], file_name="labworks.csv")),
                            ft.PopupMenuItem(text="Export PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: self.export_pdf_dialog.save_file(allowed_extensions=["pdf"], file_name="labworks.pdf")),
                            ft.PopupMenuItem(text="Import CSV", icon=ft.Icons.UPLOAD, on_click=lambda _: self.import_csv_dialog.pick_files(allowed_extensions=["csv"])),
                        ]
                    ),
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_case_click)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_data_table()
        ]

    def build_data_table(self):
        cases = LabCase.select().order_by(LabCase.sent_date.desc())
        
        if cases.count() == 0:
            return ft.Text("No active lab cases.", color=ft.Colors.GREY)

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Patient")),
                ft.DataColumn(ft.Text("Lab")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.patient_name)),
                        ft.DataCell(ft.Text(c.lab.name if c.lab else "-")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(c.status, color=ft.Colors.WHITE),
                                bgcolor=self.get_status_color(c.status),
                                padding=5, border_radius=5
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip="Details", on_click=lambda e, c=c: self.show_details_click(e, c)),
                                ft.IconButton(ft.Icons.CHECK_CIRCLE, tooltip="Mark Received", icon_color=ft.Colors.GREEN, 
                                              on_click=lambda e, c=c: self.mark_received(e, c), 
                                              visible=(c.status == "Sent")),
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda e, c=c: self.edit_case_click(e, c)),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, c=c: self.delete_case_click(e, c))
                            ])
                        ),
                    ]
                ) for c in cases
            ],
            width=float('inf'),
        )

    def get_status_color(self, status):
        if status == "Sent": return ft.Colors.ORANGE
        if status == "Received": return ft.Colors.BLUE
        if status == "Delivered": return ft.Colors.GREEN
        return ft.Colors.GREY

    def show_details_click(self, e, case):
        content = ft.Column([
            ft.Text(f"Patient: {case.patient_name}", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Lab: {case.lab.name if case.lab else 'N/A'}"),
            ft.Text(f"Work Type: {case.work_type}"),
            ft.Text(f"Status: {case.status}"),
            ft.Divider(),
            ft.Text(f"Sent Date: {case.sent_date}"),
            ft.Text(f"Due Date: {case.due_date or 'N/A'}"),
            ft.Text(f"Received Date: {case.received_date or 'N/A'}"),
            ft.Divider(),
            ft.Text(f"Notes: {case.notes or 'N/A'}"),
        ], tight=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Lab Case Details"),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda e: e.page.close(dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def add_case_click(self, e):
        dialog = LabCaseFormDialog(e.page, self.refresh_table)
        e.page.open(dialog)

    def edit_case_click(self, e, case):
        dialog = LabCaseFormDialog(e.page, self.refresh_table, case)
        e.page.open(dialog)

    def mark_received(self, e, case):
        case.status = "Received"
        case.received_date = datetime.date.today()
        case.save()
        
        # Log Activity
        from database import ActivityLog
        ActivityLog.create(
            action="Labworks", 
            details=f"Received {case.work_type} for {case.patient_name} from {case.lab.name}", 
            cost=0.0
        )

        self.refresh_table()
        e.page.snack_bar = ft.SnackBar(ft.Text(f"Marked case for {case.patient_name} as Received"))
        e.page.snack_bar.open = True
        e.page.update()

    def delete_case_click(self, e, case):
        def confirm_delete(e):
            case.delete_instance()
            self.refresh_table()
            e.page.close(dialog)
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted case for {case.patient_name}"))
            e.page.snack_bar.open = True
            e.page.update()

        def cancel_delete(e):
            e.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete case for {case.patient_name}?"),
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
            query = LabCase.select()
            fields = ["patient_name", "lab", "work_type", "sent_date", "due_date", "received_date", "status", "notes"]
            success, msg = export_to_csv(query, e.path, fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def export_pdf_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            query = LabCase.select()
            fields = ["patient_name", "lab", "work_type", "sent_date", "status"]
            success, msg = export_to_pdf(query, e.path, "Labworks Report", fields)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()

    def import_csv_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            field_map = {
                "patient_name": "patient_name",
                "lab_id": "lab_id", # Note: CSV must contain lab_id, not lab name for simplicity
                "work_type": "work_type",
                "sent_date": "sent_date",
                "due_date": "due_date",
                "received_date": "received_date",
                "status": "status",
                "notes": "notes"
            }
            success, msg = import_from_csv(LabCase, e.files[0].path, field_map)
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.update()
            self.refresh_table()
