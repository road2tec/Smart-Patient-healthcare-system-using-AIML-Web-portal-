"""
Quick script to create admin user in MongoDB
"""
from pymongo import MongoClient
from models.user import Admin
from config import MONGO_URI, DATABASE_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DATABASE_NAME]
    
    # Test connection
    client.admin.command('ping')
    print("✓ MongoDB connected")
    
    # Check if admin exists
    existing = db.users.find_one({"email": ADMIN_EMAIL})
    if existing:
        print(f"✓ Admin already exists: {ADMIN_EMAIL}")
    else:
        # Create admin
        admin = Admin(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            name=ADMIN_NAME,
            phone="1234567890"
        )
        admin_data = admin.to_dict()
        result = db.users.insert_one(admin_data)
        
        # Also add to admins collection
        admin_data['user_id'] = result.inserted_id
        admin_data.pop('_id', None)
        db.admins.insert_one(admin_data)
        
        print(f"✓ Admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nMongoDB is not running or not accessible.")
    print("Please start MongoDB or the app will use in-memory test users.")
