# Dental Clinic Inventory Management System

A desktop app for running a dental clinic's storage room. It tracks stock and expiry dates, follows instruments through sterilization, and keeps track of cases sent to outside dental labs.

Built with **Python** and **Flet** (a Flutter-based UI), with a local **SQLite** database through the **Peewee** ORM.

## Features

- **Inventory with batch tracking:** items are stored in batches with purchase and expiry dates, plus quick add, deduct and "mark used" actions
- **Alerts:** desktop notifications for items below minimum stock and batches expiring within 7 days
- **Sterilization workflow:** move instruments and equipment between sterile and contaminated states, one item at a time or in bulk
- **Lab cases:** log work sent to dental labs with sent and due dates and a status
- **Suppliers and transactions:** supplier records plus a full log of stock movements
- **Dashboard:** summary cards and a recent-activity feed
- **Import and export:** CSV import, and CSV and PDF export (ReportLab)
- **Security:** login with bcrypt-hashed passwords, Fernet-encrypted sensitive fields, and sessions that expire after 15 days

## Tech stack

Python · Flet · Peewee · SQLite · bcrypt · cryptography (Fernet) · ReportLab · plyer

## Project structure

```
main.py            app entry, theme, login/session handling
database.py        Peewee models (InventoryItem, Batch, Supplier, LabCase, ActivityLog, User)
views/             dashboard, inventory, sterilization, labworks, suppliers, transactions, settings, login
components/        app layout and sidebar
utils/             security (hashing/encryption), CSV/PDF export, notifications
```

## Run

```bash
pip install -r requirements.txt
python main.py
```

The app can also be packaged as a Windows executable with PyInstaller.
