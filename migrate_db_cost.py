from peewee import *
from database import db

def migrate():
    db.connect()
    try:
        db.execute_sql('ALTER TABLE inventoryitem ADD COLUMN cost_per_unit REAL DEFAULT 0.0')
        print("Added cost_per_unit column to inventoryitem table.")
    except OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column cost_per_unit already exists.")
        else:
            print(f"Error adding cost_per_unit: {e}")

    try:
        db.execute_sql('ALTER TABLE activitylog ADD COLUMN cost REAL DEFAULT 0.0')
        print("Added cost column to activitylog table.")
    except OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column cost already exists.")
        else:
            print(f"Error adding cost: {e}")

if __name__ == "__main__":
    migrate()
