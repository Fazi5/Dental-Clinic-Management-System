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
    category = CharField(null=True) # Dental Laboratory, Dental Supplies
    details = TextField(null=True)

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
    purpose = CharField(null=True) # Selling, Usage
    supplier = ForeignKeyField(Supplier, backref='items', null=True)

class ActivityLog(BaseModel):
    action = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    details = TextField()
    cost = FloatField(default=0.0)

class Batch(BaseModel):
    item = ForeignKeyField(InventoryItem, backref='batches')
    quantity = IntegerField(default=0)
    expiry_date = DateField(null=True)
    purchase_date = DateField(default=datetime.date.today)
    cost_per_unit = FloatField(default=0.0)
    details = TextField(null=True) # JSON or text for Company, Material, Grade
    added_date = DateTimeField(default=datetime.datetime.now)

class LabCase(BaseModel):
    patient_name = CharField()
    lab = ForeignKeyField(Supplier, backref='cases')
    work_type = CharField() # Crown, Bridge, Denture, etc.
    sent_date = DateField(default=datetime.date.today)
    due_date = DateField(null=True)
    received_date = DateField(null=True)
    status = CharField(default="Sent") # Sent, Received, Delivered
    cost = FloatField(default=0.0)
    notes = TextField(null=True)

class User(BaseModel):
    username_hash = CharField(unique=True) # SHA256 for lookup
    username_enc = CharField() # Encrypted for display
    password_hash = CharField() # bcrypt hash
    role_enc = CharField(default="gAAAAAB...") # Encrypted role
    security_question_enc = CharField(null=True) # Encrypted
    security_answer_hash = CharField(null=True) # bcrypt hash
    permissions_enc = TextField(null=True) # Encrypted

def initialize_db():
    db.connect()
    db.create_tables([Supplier, InventoryItem, ActivityLog, Batch, LabCase, User])
    
    # Seed some initial data if empty
    if Supplier.select().count() == 0:
        Supplier.create(name="Dental Depot Inc.", email="orders@dentaldepot.com")
        Supplier.create(name="MediSupply Co.", email="sales@medisupply.com")

    # Seed Admin User
    if User.select().count() == 0:
        import bcrypt
        from utils.security import encrypt_data, hash_data
        
        # Default: admin / admin123
        pass_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        ans_hash = bcrypt.hashpw("Enamel".lower().encode('utf-8'), bcrypt.gensalt())
        
        User.create(
            username_hash=hash_data("admin"),
            username_enc=encrypt_data("admin"),
            password_hash=pass_hash.decode('utf-8'), 
            role_enc=encrypt_data("admin"),
            security_question_enc=encrypt_data("What is the hardest substance in the human body?"),
            security_answer_hash=ans_hash.decode('utf-8'),
            permissions_enc=encrypt_data("all")
        )

if __name__ == "__main__":
    initialize_db()
