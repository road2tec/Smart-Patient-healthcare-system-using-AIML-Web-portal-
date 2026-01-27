# Authentication Routes for Smart Patient Healthcare System
# Handles user registration, login, and authentication

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
from datetime import datetime, timedelta
import sys
import os
import json
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (MONGO_URI, DATABASE_NAME, COLLECTIONS, 
                    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, OTP_EXPIRY_MINUTES)
from models.user import User, Patient, Doctor, Admin

def get_current_user():
    """Helper to get current user identity as dict"""
    identity = get_jwt_identity()
    if isinstance(identity, str):
        try:
            return json.loads(identity)
        except:
            return {"id": identity}
    return identity

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """Send OTP via email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = 'OTP for Patient Registration - Smart Healthcare System'
        
        body = f"""
        <html>
            <body>
                <h2>Smart Patient Healthcare System</h2>
                <p>Your OTP for registration is: <strong style="font-size: 24px; color: #007bff;">{otp}</strong></p>
                <p>This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Smart Healthcare Team</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server with timeout
        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        print("Starting TLS encryption...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print(f"Logged in as {SMTP_USER}")
        server.send_message(msg)
        server.quit()
        
        print(f"✓ OTP email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send OTP email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@auth_bp.route('/register/request-otp', methods=['POST'])
def request_otp():
    """
    Request OTP for patient registration
    Expected JSON: { name, email, password, phone, age, gender, blood_group, address }
    """
    print("\n" + "="*60)
    print("OTP REQUEST RECEIVED")
    print("="*60)
    try:
        data = request.get_json()
        print(f"Request data: {data.get('email') if data else 'No data'}")
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"{field} is required"
                }), 400
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            return jsonify({
                "success": False,
                "message": "Invalid email format"
            }), 400
        
        # Check if email already exists
        existing_user = db[COLLECTIONS['users']].find_one({"email": data['email']})
        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 400
        
        # Generate OTP
        otp = generate_otp()
        print(f"Generated OTP: {otp}")
        expiry_time = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        
        # Store OTP and registration data temporarily
        otp_data = {
            "email": data['email'],
            "otp": otp,
            "registration_data": {
                "name": data['name'],
                "email": data['email'],
                "password": data['password'],
                "phone": data.get('phone'),
                "age": data.get('age'),
                "gender": data.get('gender'),
                "blood_group": data.get('blood_group'),
                "address": data.get('address')
            },
            "expiry_time": expiry_time,
            "created_at": datetime.utcnow(),
            "verified": False
        }
        
        # Delete any existing OTP for this email
        db[COLLECTIONS['otp_verifications']].delete_many({"email": data['email']})
        
        # Insert new OTP
        result = db[COLLECTIONS['otp_verifications']].insert_one(otp_data)
        print(f"OTP stored in database: {result.inserted_id}")
        
        # Send OTP via email
        print(f"Attempting to send OTP to: {data['email']}")
        email_sent = send_otp_email(data['email'], otp)
        print(f"Email sent status: {email_sent}")
        
        if not email_sent:
            print("❌ EMAIL SENDING FAILED")
            return jsonify({
                "success": False,
                "message": "Failed to send OTP email. Please try again."
            }), 500
        
        print("✅ OTP REQUEST SUCCESSFUL")
        print("="*60 + "\n")
        return jsonify({
            "success": True,
            "message": f"OTP sent to {data['email']}. Please verify to complete registration.",
            "email": data['email']
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Registration request failed: {str(e)}"
        }), 500


@auth_bp.route('/register/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP and complete registration
    Expected JSON: { email, otp }
    """
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('otp'):
            return jsonify({
                "success": False,
                "message": "Email and OTP are required"
            }), 400
        
        # Find OTP record
        otp_record = db[COLLECTIONS['otp_verifications']].find_one({
            "email": data['email'],
            "verified": False
        })
        
        if not otp_record:
            return jsonify({
                "success": False,
                "message": "No OTP request found for this email"
            }), 404
        
        # Check if OTP expired
        if datetime.utcnow() > otp_record['expiry_time']:
            db[COLLECTIONS['otp_verifications']].delete_one({"_id": otp_record['_id']})
            return jsonify({
                "success": False,
                "message": "OTP expired. Please request a new one."
            }), 400
        
        # Verify OTP
        if otp_record['otp'] != data['otp']:
            return jsonify({
                "success": False,
                "message": "Invalid OTP"
            }), 400
        
        # OTP verified - proceed with registration
        reg_data = otp_record['registration_data']
        
        # Create patient object
        patient = Patient(
            email=reg_data['email'],
            password=reg_data['password'],
            name=reg_data['name'],
            phone=reg_data.get('phone'),
            address=reg_data.get('address'),
            age=reg_data.get('age'),
            gender=reg_data.get('gender'),
            blood_group=reg_data.get('blood_group')
        )
        
        # Insert into users collection
        user_data = patient.to_dict()
        user_result = db[COLLECTIONS['users']].insert_one(user_data)
        
        # Also insert into patients collection with user reference
        patient_data = patient.to_dict()
        patient_data['user_id'] = user_result.inserted_id
        db[COLLECTIONS['patients']].insert_one(patient_data)
        
        # Mark OTP as verified
        db[COLLECTIONS['otp_verifications']].update_one(
            {"_id": otp_record['_id']},
            {"$set": {"verified": True}}
        )
        
        # Generate access token
        access_token = create_access_token(identity={
            "id": str(user_result.inserted_id),
            "email": reg_data['email'],
            "role": "patient",
            "name": reg_data['name']
        })
        
        return jsonify({
            "success": True,
            "message": "Registration successful! Email verified.",
            "token": access_token,
            "user": {
                "id": str(user_result.inserted_id),
                "name": reg_data['name'],
                "email": reg_data['email'],
                "role": "patient"
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"OTP verification failed: {str(e)}"
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Legacy register endpoint - redirects to OTP flow
    Expected JSON: { name, email, password, phone, age, gender, blood_group, address }
    """
    return jsonify({
        "success": False,
        "message": "Please use /register/request-otp endpoint for registration"
    }), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user (patient, doctor, or admin)
    Expected JSON: { email, password, role (optional) }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                "success": False,
                "message": "Email and password are required"
            }), 400
        
        # Try MongoDB first, then fall back to in-memory users
        user = None
        try:
            user = db[COLLECTIONS['users']].find_one({"email": data['email']})
        except Exception as db_error:
            # MongoDB not available, use in-memory test users
            pass
        
        # If MongoDB didn't work, try in-memory users
        if not user:
            # Import app module to access test_users
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import app as app_module
            test_users = getattr(app_module, 'test_users', {})
            user = test_users.get(data['email'])
        
        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401
        
        # Verify password
        if not User.verify_password(data['password'], user['password']):
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401
        
        # Check if user is active
        if not user.get('is_active', True):
            return jsonify({
                "success": False,
                "message": "Account is deactivated"
            }), 401
        
        # Generate access token
        access_token = create_access_token(identity={
            "id": str(user['_id']),
            "email": user['email'],
            "role": user['role'],
            "name": user['name']
        })
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": access_token,
            "user": {
                "id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "role": user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Login failed: {str(e)}"
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current logged in user details"""
    try:
        current_user = get_current_user()
        user = db[COLLECTIONS['users']].find_one(
            {"_id": ObjectId(current_user['id'])},
            {"password": 0}  # Exclude password
        )
        
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        user['_id'] = str(user['_id'])
        
        return jsonify({
            "success": True,
            "user": user
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error fetching user: {str(e)}"
        }), 500


@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        # Fields that can be updated
        update_fields = {}
        allowed_fields = ['name', 'phone', 'address', 'age', 'gender', 'blood_group']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        update_fields['updated_at'] = datetime.utcnow()
        
        # Update user in users collection
        db[COLLECTIONS['users']].update_one(
            {"_id": ObjectId(current_user['id'])},
            {"$set": update_fields}
        )
        
        # If patient, also update patients collection
        if current_user['role'] == 'patient':
            db[COLLECTIONS['patients']].update_one(
                {"user_id": ObjectId(current_user['id'])},
                {"$set": update_fields}
            )
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating profile: {str(e)}"
        }), 500


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                "success": False,
                "message": "Current password and new password are required"
            }), 400
        
        # Get user
        user = db[COLLECTIONS['users']].find_one({"_id": ObjectId(current_user['id'])})
        
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Verify current password
        if not User.verify_password(data['current_password'], user['password']):
            return jsonify({
                "success": False,
                "message": "Current password is incorrect"
            }), 400
        
        # Hash new password
        new_password_hash = User.hash_password(data['new_password'])
        
        # Update password
        db[COLLECTIONS['users']].update_one(
            {"_id": ObjectId(current_user['id'])},
            {"$set": {
                "password": new_password_hash,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error changing password: {str(e)}"
        }), 500
