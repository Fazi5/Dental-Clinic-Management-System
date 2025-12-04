import flet as ft
import os
import time
import datetime
import threading
from components.app_layout import AppLayout
from views.dashboard import DashboardView
from views.inventory import InventoryView
from views.suppliers import SupplierView
from views.sterilization import SterilizationView
from views.transactions import TransactionsView
from database import initialize_db, User
from utils.notifications import NotificationManager
from utils.security import decrypt_data
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main(page: ft.Page):
    initialize_db()
    page.title = "Faizan Dental Clinic's Storage"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Use absolute path for icon to avoid resolution issues
    icon_path = resource_path(os.path.join("assets", "icon.ico"))
    page.window_icon = icon_path
    
    # "Clean Clinical" Theme Colors
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.TEAL_600,
            primary_container=ft.Colors.TEAL_100,
            secondary=ft.Colors.CYAN_600,
            surface=ft.Colors.WHITE,
            background=ft.Colors.GREY_50,
        )
    )

    # Authentication State
    def check_auth():
        if not page.client_storage.contains_key("user_id"):
            return False
        
        # Check Expiry (15 days)
        login_time_str = page.client_storage.get("login_timestamp")
        if login_time_str:
            try:
                login_time = datetime.datetime.fromisoformat(login_time_str)
                if datetime.datetime.now() - login_time > datetime.timedelta(days=15):
                    logout() # Expired
                    return False
            except:
                logout() # Invalid timestamp
                return False
        else:
            # If no timestamp (legacy session), force logout to set it
            logout()
            return False
            
        return True

    def logout():
        page.client_storage.remove("user_id")
        page.client_storage.remove("user_role")
        page.client_storage.remove("login_timestamp")
        page.session.clear()
        page.clean()
        show_login()

    def on_login_success(user):
        page.client_storage.set("user_id", user.id)
        page.client_storage.set("user_role", user.role)
        page.client_storage.set("login_timestamp", datetime.datetime.now().isoformat())
        page.clean()
        show_app_layout()

    def show_login():
        from views.login import LoginView
        page.add(LoginView(page, on_login_success))
        page.update()

    def show_app_layout():
        # Get current user for context
        user_id = page.client_storage.get("user_id")
        try:
            current_user = User.get_by_id(user_id)
            # Decrypt for runtime use
            current_user.role = decrypt_data(current_user.role_enc)
            current_user.permissions = decrypt_data(current_user.permissions_enc)
        except:
            logout()
            return

        def on_nav_change(index):
            if index == "logout":
                logout()
                return
            
            # Check Permissions
            perms = current_user.permissions or ""
            is_admin = current_user.role == "admin"
            
            def has_perm(p):
                return is_admin or "all" in perms or p in perms

            if index == 0:
                layout.set_content(DashboardView(on_navigate=navigate_to))
            elif index == 1:
                if has_perm("view_inventory"):
                    layout.set_content(InventoryView())
                else:
                    layout.set_content(ft.Text("Access Denied", color=ft.Colors.RED))
            elif index == 2:
                if has_perm("view_suppliers"):
                    layout.set_content(SupplierView())
                else:
                    layout.set_content(ft.Text("Access Denied", color=ft.Colors.RED))
            elif index == 3:
                if has_perm("view_sterilization"):
                    layout.set_content(SterilizationView())
                else:
                    layout.set_content(ft.Text("Access Denied", color=ft.Colors.RED))
            elif index == 4:
                if has_perm("view_transactions"):
                    layout.set_content(TransactionsView())
                else:
                    layout.set_content(ft.Text("Access Denied", color=ft.Colors.RED))
            elif index == 5:
                if has_perm("view_labworks"):
                    from views.labworks import LabworksView
                    layout.set_content(LabworksView())
                else:
                    layout.set_content(ft.Text("Access Denied", color=ft.Colors.RED))
            elif index == 6: # Settings
                if is_admin:
                    from views.settings import SettingsView
                    layout.set_content(SettingsView(page, current_user))
                else:
                    layout.set_content(ft.Text("Access Denied", color=ft.Colors.RED))

        def navigate_to(index):
            layout.sidebar.select_by_original_index(index)
            on_nav_change(index)

        layout = AppLayout(page, on_nav_change, DashboardView(on_navigate=navigate_to), current_user)
        page.add(layout)
        page.update()

    # Splash Screen Logic
    splash_content = ft.Container(
        content=ft.Column(
            [
                ft.Image(src="icon.ico", width=300, height=300, fit=ft.ImageFit.CONTAIN),
                ft.ProgressRing(width=30, height=30, color=ft.Colors.TEAL),
                ft.Text("Loading System...", color=ft.Colors.GREY_700)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=ft.Colors.WHITE
    )
    
    page.add(splash_content)
    page.update()
    
    time.sleep(3) # Show splash for 3 seconds
    
    page.clean()
    
    if check_auth():
        show_app_layout()
    else:
        show_login()

    # Background Notification Service
    def run_background_checks():
        while True:
            # Check every 60 minutes
            time.sleep(3600) 
            NotificationManager().check_and_notify()

    # Start background thread as daemon so it kills when app closes
    threading.Thread(target=run_background_checks, daemon=True).start()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
