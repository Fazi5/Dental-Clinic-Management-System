import flet as ft
import bcrypt
from database import User

class LoginView(ft.Container):
    def __init__(self, page, on_login_success):
        super().__init__()
        self.page = page
        self.on_login_success = on_login_success
        self.expand = True
        self.alignment = ft.alignment.center
        self.bgcolor = ft.Colors.GREY_100
        
        self.username_field = ft.TextField(
            label="Username", 
            width=300, 
            prefix_icon=ft.Icons.PERSON,
            autofocus=True
        )
        self.password_field = ft.TextField(
            label="Password", 
            width=300, 
            password=True, 
            can_reveal_password=True, 
            prefix_icon=ft.Icons.LOCK,
            on_submit=self.login_click
        )
        self.login_button = ft.ElevatedButton(
            text="Login", 
            width=300, 
            on_click=self.login_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                padding=15
            )
        )
        self.error_text = ft.Text("", color=ft.Colors.RED, size=14)

        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Image(src="icon.ico", width=80, height=80),
                    ft.Text("Faizan Dental Clinic", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_800),
                    ft.Text("Storage Management System", size=16, color=ft.Colors.GREY_700),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.username_field,
                    self.password_field,
                    ft.TextButton("Forgot Password?", on_click=self.forgot_password_click),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.login_button,
                    self.error_text
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            width=400,
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLUE_GREY_100,
            )
        )

    def login_click(self, e):
        username = self.username_field.value
        password = self.password_field.value

        if not username or not password:
            self.error_text.value = "Please enter both username and password"
            self.error_text.update()
            return

        try:
            from utils.security import hash_data, decrypt_data
            
            # Lookup by hash
            user_hash = hash_data(username)
            user = User.get(User.username_hash == user_hash)
            
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Decrypt role and permissions for session
                user.role = decrypt_data(user.role_enc)
                user.permissions = decrypt_data(user.permissions_enc)
                self.on_login_success(user)
            else:
                self.error_text.value = "Invalid username or password"
                self.error_text.update()
        except User.DoesNotExist:
            self.error_text.value = "Invalid username or password"
            self.error_text.update()
        except Exception as ex:
            self.error_text.value = f"An error occurred: {ex}"
            self.error_text.update()

    def forgot_password_click(self, e):
        username_field = ft.TextField(label="Username", autofocus=True)
        question_text = ft.Text("Security Question: ", visible=False, weight=ft.FontWeight.BOLD)
        answer_field = ft.TextField(label="Answer", visible=False)
        new_pass_field = ft.TextField(label="New Password", password=True, can_reveal_password=True, visible=False)
        
        current_user = [None] # Mutable container for closure

        def verify_user(e):
            try:
                from utils.security import hash_data, decrypt_data
                user_hash = hash_data(username_field.value)
                user = User.get(User.username_hash == user_hash)
                
                if not user.security_question_enc or not user.security_answer_hash:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Recovery not set up for this user."))
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

                current_user[0] = user
                question = decrypt_data(user.security_question_enc)
                question_text.value = f"Q: {question}"
                question_text.visible = True
                answer_field.visible = True
                verify_btn.visible = False
                check_ans_btn.visible = True
                dialog.update()
            except User.DoesNotExist:
                self.page.snack_bar = ft.SnackBar(ft.Text("User not found"))
                self.page.snack_bar.open = True
                self.page.update()

        def check_answer(e):
            if not answer_field.value:
                return
            
            user = current_user[0]
            if bcrypt.checkpw(answer_field.value.lower().encode('utf-8'), user.security_answer_hash.encode('utf-8')):
                new_pass_field.visible = True
                check_ans_btn.visible = False
                reset_btn.visible = True
                dialog.update()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Incorrect Answer"))
                self.page.snack_bar.open = True
                self.page.update()

        def reset_password(e):
            if not new_pass_field.value:
                return
            
            user = current_user[0]
            hashed = bcrypt.hashpw(new_pass_field.value.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = hashed.decode('utf-8')
            user.save()
            
            self.page.close(dialog)
            self.page.snack_bar = ft.SnackBar(ft.Text("Password Reset Successfully"))
            self.page.snack_bar.open = True
            self.page.update()

        verify_btn = ft.ElevatedButton("Next", on_click=verify_user)
        check_ans_btn = ft.ElevatedButton("Verify Answer", on_click=check_answer, visible=False)
        reset_btn = ft.ElevatedButton("Reset Password", on_click=reset_password, visible=False)

        dialog = ft.AlertDialog(
            title=ft.Text("Forgot Password"),
            content=ft.Column([
                username_field,
                question_text,
                answer_field,
                new_pass_field
            ], tight=True, width=300),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                verify_btn,
                check_ans_btn,
                reset_btn
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dialog)
