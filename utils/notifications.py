from plyer import notification
from database import InventoryItem, Batch, LabCase
import datetime
import threading

class NotificationManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(NotificationManager, cls).__new__(cls)
        return cls._instance

    def send_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Faizan Dental Clinic",
                app_icon="assets/icon.ico", # Ensure this path is correct relative to execution
                timeout=10
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")

    def check_and_notify(self):
        print("Checking for alerts...")
        alerts = []

        # 1. Low Stock
        low_stock_count = InventoryItem.select().where(InventoryItem.quantity < InventoryItem.min_stock).count()
        if low_stock_count > 0:
            alerts.append(f"{low_stock_count} items are running low on stock.")

        # 2. Expiry (within 7 days)
        today = datetime.date.today()
        next_week = today + datetime.timedelta(days=7)
        expiry_count = Batch.select().where(
            (Batch.expiry_date >= today) & 
            (Batch.expiry_date <= next_week) & 
            (Batch.quantity > 0)
        ).count()
        if expiry_count > 0:
            alerts.append(f"{expiry_count} batches are expiring within 7 days.")

        # 3. Sterilization Needed
        sterilization_count = InventoryItem.select().where(InventoryItem.quantity_used > 0).count()
        if sterilization_count > 0:
            alerts.append(f"{sterilization_count} items need sterilization.")

        # 4. Labworks Due (Today or Tomorrow)
        tomorrow = today + datetime.timedelta(days=1)
        labworks_count = LabCase.select().where(
            (LabCase.due_date <= tomorrow) & 
            (LabCase.status != 'Received') &
            (LabCase.status != 'Delivered')
        ).count()
        if labworks_count > 0:
            alerts.append(f"{labworks_count} lab cases are due soon.")

        # Send Notifications
        if alerts:
            full_message = "\n".join(alerts)
            self.send_notification("System Alerts", full_message)
        else:
            print("No alerts found.")
