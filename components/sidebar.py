import flet as ft

class Sidebar(ft.NavigationRail):
    def __init__(self, page, on_nav_change, current_user=None):
        super().__init__()
        self.page = page
        self.on_nav_change = on_nav_change # Callback for navigation
        self.label_type = ft.NavigationRailLabelType.ALL
        self.min_width = 100
        self.min_extended_width = 400
        self.group_alignment = -0.9
        self.current_user = current_user
        
        # Define all possible destinations with their required permission
        # (Icon, SelectedIcon, Label, Permission)
        all_destinations = [
            (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, "Dashboard", "view_dashboard"), # Always visible if logged in? Or check perm
            (ft.Icons.INVENTORY_2_OUTLINED, ft.Icons.INVENTORY_2, "Inventory", "view_inventory"),
            (ft.Icons.PEOPLE_OUTLINE, ft.Icons.PEOPLE, "Suppliers", "view_suppliers"),
            (ft.Icons.CLEANING_SERVICES_OUTLINED, ft.Icons.CLEANING_SERVICES, "Sterilization", "view_sterilization"),
            (ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG, "Transactions", "view_transactions"),
            (ft.Icons.MEDICAL_SERVICES_OUTLINED, ft.Icons.MEDICAL_SERVICES, "Labworks", "view_labworks"),
            (ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, "Settings", "admin"), # Admin only
        ]

        self.destinations = []
        self.nav_map = {} # Map filtered index to original index (0-6)
        
        if self.current_user:
            perms = self.current_user.permissions or ""
            is_admin = self.current_user.role == "admin"
            
            for i, (icon, sel_icon, label, perm) in enumerate(all_destinations):
                has_perm = is_admin or "all" in perms or perm in perms or perm == "view_dashboard" # Dashboard always visible for now
                
                if has_perm:
                    self.destinations.append(
                        ft.NavigationRailDestination(
                            icon=icon,
                            selected_icon=sel_icon,
                            label=label
                        )
                    )
                    # Map the new index (len-1) to the original index (i)
                    self.nav_map[len(self.destinations)-1] = i
        self.on_change = self.nav_change
        
        # Logout Button
        self.logout_button = ft.IconButton(
            icon=ft.Icons.LOGOUT, 
            tooltip="Logout", 
            on_click=lambda e: self.on_nav_change("logout"),
            icon_color=ft.Colors.RED
        )
        
        # Add logout button to the bottom
        self.trailing = ft.Container(
            content=self.logout_button,
            alignment=ft.alignment.bottom_center,
            padding=ft.padding.only(bottom=20)
        )

    def nav_change(self, e):
        # Translate filtered index to original index
        selected_idx = e.control.selected_index
        if selected_idx in self.nav_map:
            original_idx = self.nav_map[selected_idx]
            self.on_nav_change(original_idx)

    def select_by_original_index(self, original_index):
        # Find the filtered index that maps to this original index
        for filtered_idx, orig_idx in self.nav_map.items():
            if orig_idx == original_index:
                self.selected_index = filtered_idx
                self.update()
                return
