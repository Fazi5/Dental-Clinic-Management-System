from peewee import *
import datetime

db = SqliteDatabase('dental_clinic.db')

class BaseModel(Model):
    class Meta:
        database = db

class Supplier(BaseModel):
    name = CharField()
    contact_info = TextField(null=True)
    email = CharField(null=True)
    phone = CharField(null=True)
    location = CharField(null=True)

class InventoryItem(BaseModel):
    name = CharField()
    category = CharField() # Equipment, Instrument, Consumable
    quantity = IntegerField(default=0)
    quantity_used = IntegerField(default=0)
    quantity_sterilizing = IntegerField(default=0)
    unit = CharField() # pcs, boxes, liters
    min_stock = IntegerField(default=5)
    cost_per_unit = FloatField(default=0.0)
    expiry_date = DateField(null=True)
    sterilization_status = CharField(null=True) # Sterile, Used, In-Autoclave
    supplier = ForeignKeyField(Supplier, backref='items', null=True)

class ActivityLog(BaseModel):
    action = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    details = TextField()
    cost = FloatField(default=0.0)

def initialize_db():
    db.connect()
    db.create_tables([Supplier, InventoryItem, ActivityLog])
    
    # Seed some initial data if empty
    if Supplier.select().count() == 0:
        Supplier.create(name="Dental Depot Inc.", email="orders@dentaldepot.com")
        Supplier.create(name="MediSupply Co.", email="sales@medisupply.com")

if __name__ == "__main__":
    initialize_db()
