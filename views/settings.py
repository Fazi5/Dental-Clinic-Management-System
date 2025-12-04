import flet as ft
import bcrypt
from database import User
from utils.security import decrypt_data, encrypt_data, hash_data

class SettingsView(ft.Column):
    def __init__(self, page, current_user):
        super().__init__()
        self.page = page
        self.current_user = current_user
        self.expand = True
        
        # Access Control
        if self.current_user.role != "admin":
            self.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.BLOCK, size=50, color=ft.Colors.RED),
                        ft.Text("Access Denied", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("You do not have permission to view this page.", size=16),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ]
            return

        self.controls = [
            ft.Row([
                ft.Text("User Management", size=30, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Add User", icon=ft.Icons.ADD, on_click=self.add_user_click)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.build_user_table()
        ]

    def build_user_table(self):
        users = User.select()
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(decrypt_data(user.username_enc))),
                        ft.DataCell(ft.Text(decrypt_data(user.role_enc))),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.LOCK_RESET, tooltip="Reset Password", on_click=lambda e, u=user: self.reset_password_click(e, u)),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, 
                                              disabled=(decrypt_data(user.username_enc) == "admin" or user.id == self.current_user.id),
                                              on_click=lambda e, u=user: self.delete_user_click(e, u))
                            ])
                        ),
                    ]
                ) for user in users
            ],
            width=float('inf'),
        )

    def refresh_table(self):
        self.controls[-1] = self.build_user_table()
        self.update()

    def add_user_click(self, e):
        username_field = ft.TextField(label="Username")
        password_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
        role_field = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("user"),
                ft.dropdown.Option("admin"),
            ],
            value="user"
        )

        security_question_field = ft.TextField(label="Security Question")
        security_answer_field = ft.TextField(label="Security Answer", password=True, can_reveal_password=True)

        # Permissions
        permissions_options = {
            "Inventory": ["view_inventory", "edit_inventory"],
            "Suppliers": ["view_suppliers", "edit_suppliers"],
            "Sterilization": ["view_sterilization", "edit_sterilization"],
            "Transactions": ["view_transactions", "edit_transactions"],
            "Labworks": ["view_labworks", "edit_labworks"],
        }
        
        permission_checkboxes = {}
        permission_controls = []
        
        for category, perms in permissions_options.items():
            permission_controls.append(ft.Text(category, weight=ft.FontWeight.BOLD))
            row = []
            for p in perms:
                label = "View" if "view" in p else "Edit"
                cb = ft.Checkbox(label=label, value=True)
                permission_checkboxes[p] = cb
                row.append(cb)
            permission_controls.append(ft.Row(row))

        def save_user(e):
            if not username_field.value or not password_field.value:
                self.page.snack_bar = ft.SnackBar(ft.Text("Username and Password are required"))
                self.page.snack_bar.open = True
                self.page.update()
                return
                
            if not security_question_field.value or not security_answer_field.value:
                self.page.snack_bar = ft.SnackBar(ft.Text("Security Question and Answer are required"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            try:
                hashed = bcrypt.hashpw(password_field.value.encode('utf-8'), bcrypt.gensalt())
                ans_hashed = bcrypt.hashpw(security_answer_field.value.lower().encode('utf-8'), bcrypt.gensalt())
                
                # Gather permissions
                selected_perms = []
                if role_field.value == "admin":
                    selected_perms = ["all"]
                else:
                    for p, cb in permission_checkboxes.items():
                        if cb.value:
                            selected_perms.append(p)
                
                perms_str = ",".join(selected_perms)
                
                User.create(
                    username_hash=hash_data(username_field.value),
                    username_enc=encrypt_data(username_field.value),
                    password_hash=hashed.decode('utf-8'),
                    role_enc=encrypt_data(role_field.value),
                    security_question_enc=encrypt_data(security_question_field.value),
                    security_answer_hash=ans_hashed.decode('utf-8'),
                    permissions_enc=encrypt_data(perms_str)
                )
                self.page.close(dialog)
                self.refresh_table()
                self.page.snack_bar = ft.SnackBar(ft.Text(f"User {username_field.value} created"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
                self.page.snack_bar.open = True
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Add User"),
            content=ft.Column([
                username_field, 
                password_field, 
                role_field,
                ft.Divider(),
                ft.Text("Security Recovery", weight=ft.FontWeight.BOLD),
                security_question_field,
                security_answer_field,
                ft.Divider(),
                ft.Text("Permissions (for User role)", weight=ft.FontWeight.BOLD),
                *permission_controls
            ], tight=True, width=400, scroll=ft.ScrollMode.AUTO, height=500),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Create", on_click=save_user)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dialog)

    def reset_password_click(self, e, user):
        password_field = ft.TextField(label="New Password", password=True, can_reveal_password=True)

        def save_password(e):
            if not password_field.value:
                return

            try:
                hashed = bcrypt.hashpw(password_field.value.encode('utf-8'), bcrypt.gensalt())
                user.password_hash = hashed.decode('utf-8')
                user.save()
                self.page.close(dialog)
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Password reset for {user.username}"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
                self.page.snack_bar.open = True
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Reset Password for {user.username}"),
            content=password_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Save", on_click=save_password)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dialog)

    def delete_user_click(self, e, user):
        def confirm_delete(e):
            user.delete_instance()
            self.refresh_table()
            self.page.close(dialog)
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted user {user.username}"))
            self.page.snack_bar.open = True
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete user {user.username}?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)
