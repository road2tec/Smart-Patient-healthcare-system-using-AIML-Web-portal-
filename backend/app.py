"""
Smart Patient Healthcare System - Main Flask Application
This is the main entry point for the backend API server.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from datetime import datetime
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (MONGO_URI, DATABASE_NAME, JWT_SECRET_KEY, 
                    JWT_ACCESS_TOKEN_EXPIRES, FLASK_DEBUG, FLASK_HOST, FLASK_PORT)
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES

# Initialize extensions with proper CORS settings
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)
jwt = JWTManager(app)

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Global test users store (for when MongoDB is not available)
test_users = {}

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(patient_bp, url_prefix='/api')
app.register_blueprint(doctor_bp, url_prefix='/api/doctor')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"success": False, "message": "Token has expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"success": False, "message": "Invalid token"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"success": False, "message": "Authorization required"}), 401

# JWT identity serialization - convert dict to JSON string
import json

@jwt.user_identity_loader
def user_identity_lookup(user):
    if isinstance(user, dict):
        return json.dumps(user)
    return user

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    try:
        return json.loads(identity)
    except:
        return identity

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Try to ping MongoDB, but don't fail if it's not available
        client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected - {str(e)[:50]}..."
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Smart Patient Healthcare System API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/register, /api/login",
            "patient": "/api/symptoms/predict, /api/appointments/*",
            "doctor": "/api/doctor/appointments, /api/doctor/update-status",
            "admin": "/api/admin/users, /api/admin/add-doctor"
        }
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error"}), 500

def init_database():
    """Initialize database with collections and default admin"""
    try:
        from models.user import Admin
        from config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME
        
        # Test database connection
        client.admin.command('ping')
        
        # All collections including admins
        collections = ['users', 'patients', 'doctors', 'admins', 'appointments', 'symptoms_logs', 'admin_logs']
        
        for coll in collections:
            if coll not in db.list_collection_names():
                db.create_collection(coll)
                print(f"Created collection: {coll}")
        
        # Create default admin if not exists (credentials from .env)
        if not db.users.find_one({"email": ADMIN_EMAIL}):
            admin = Admin(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                name=ADMIN_NAME,
                phone="1234567890"
            )
            admin_data = admin.to_dict()
            # Insert into users collection
            result = db.users.insert_one(admin_data)
            # Also insert into admins collection with user_id reference
            admin_data['user_id'] = result.inserted_id
            admin_data.pop('_id', None)
            db.admins.insert_one(admin_data)
            print(f"Default admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
            
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("Creating in-memory user store for testing...")
        
        # Create a simple in-memory user store for testing
        global test_users
        test_users = {
            "admin@healthcare.com": {
                "_id": "admin_test_id",
                "email": "admin@healthcare.com",
                "password": "simple_hash_admin123",  # Using our simple hash
                "name": "Test Admin",
                "role": "admin",
                "phone": "1234567890",
                "is_active": True
            },
            "patient@test.com": {
                "_id": "patient_test_id", 
                "email": "patient@test.com",
                "password": "simple_hash_patient123",
                "name": "Test Patient", 
                "role": "patient",
                "phone": "9876543210",
                "is_active": True
            }
        }
        print("Test users created:")
        print("Admin: admin@healthcare.com / admin123")
        print("Patient: patient@test.com / patient123")

if __name__ == '__main__':
    print("="*60)
    print("Smart Patient Healthcare System - Backend Server")
    print("="*60)
    
    # Initialize database (safe: continue if MongoDB not available)
    try:
        init_database()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Creating in-memory user store for testing...")
        
        # Ensure test_users is created
        test_users["admin@healthcare.com"] = {
            "_id": "admin_test_id",
            "email": "admin@healthcare.com",
            "password": "simple_hash_admin123",
            "name": "Test Admin",
            "role": "admin",
            "phone": "1234567890",
            "is_active": True
        }
        test_users["patient@test.com"] = {
            "_id": "patient_test_id", 
            "email": "patient@test.com",
            "password": "simple_hash_patient123",
            "name": "Test Patient", 
            "role": "patient",
            "phone": "9876543210",
            "is_active": True
        }
        print("✓ Test users created:")
        print("  Admin: admin@healthcare.com / admin123")
        print("  Patient: patient@test.com / patient123")
    
    print(f"\nServer running at: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"MongoDB: {MONGO_URI}")
    print("="*60)
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
