from peewee import *
from database import db

def migrate():
    db.connect()
    try:
        db.execute_sql('ALTER TABLE inventoryitem ADD COLUMN quantity_used INTEGER DEFAULT 0')
        print("Added quantity_used column to inventoryitem table.")
    except OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column quantity_used already exists.")
        else:
            print(f"Error adding quantity_used: {e}")

    try:
        db.execute_sql('ALTER TABLE inventoryitem ADD COLUMN quantity_sterilizing INTEGER DEFAULT 0')
        print("Added quantity_sterilizing column to inventoryitem table.")
    except OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column quantity_sterilizing already exists.")
        else:
            print(f"Error adding quantity_sterilizing: {e}")

if __name__ == "__main__":
    migrate()
