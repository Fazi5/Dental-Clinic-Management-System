import flet as ft
print("Checking ft.colors...")
try:
    print(ft.colors.RED)
except Exception as e:
    print(f"ft.colors failed: {e}")

print("Checking ft.Colors...")
try:
    print(ft.Colors.RED)
except Exception as e:
    print(f"ft.Colors failed: {e}")
