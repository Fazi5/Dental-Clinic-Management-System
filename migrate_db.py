from peewee import *
from database import db

def migrate():
    db.connect()
    try:
        db.execute_sql('ALTER TABLE supplier ADD COLUMN location VARCHAR(255)')
        print("Added location column to supplier table.")
    except OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists.")
        else:
            print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
