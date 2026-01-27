# Doctor Routes for Smart Patient Healthcare System
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGO_URI, DATABASE_NAME, COLLECTIONS

def get_current_user():
    """Helper to get current user identity as dict"""
    identity = get_jwt_identity()
    if isinstance(identity, str):
        try:
            return json.loads(identity)
        except:
            return {"id": identity}
    return identity

doctor_bp = Blueprint('doctor', __name__)
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

def is_doctor(u): return u.get('role') == 'doctor'

@doctor_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_doctor_appointments():
    try:
        current_user = get_current_user()
        if not is_doctor(current_user):
            return jsonify({"success": False, "message": "Access denied"}), 403
        status = request.args.get('status')
        query = {"doctor_id": current_user['id']}
        if status: query["status"] = status
        appointments = list(db[COLLECTIONS['appointments']].find(query).sort("appointment_date", 1))
        
        for apt in appointments:
            apt['_id'] = str(apt['_id'])
            
            # Convert datetime objects to strings
            if 'created_at' in apt and hasattr(apt['created_at'], 'isoformat'):
                apt['created_at'] = apt['created_at'].isoformat()
            if 'updated_at' in apt and hasattr(apt['updated_at'], 'isoformat'):
                apt['updated_at'] = apt['updated_at'].isoformat()
            
            # Get patient details - try multiple ways
            if apt.get('patient_id'):
                patient_id = apt['patient_id']
                patient = None
                
                # Try finding in patients collection by user_id
                try:
                    patient = db[COLLECTIONS['patients']].find_one(
                        {"user_id": ObjectId(patient_id)}, {"password": 0}
                    )
                except:
                    pass
                
                # Try finding by _id in patients
                if not patient:
                    try:
                        patient = db[COLLECTIONS['patients']].find_one(
                            {"_id": ObjectId(patient_id)}, {"password": 0}
                        )
                    except:
                        pass
                
                # Try finding in users collection
                if not patient:
                    try:
                        patient = db[COLLECTIONS['users']].find_one(
                            {"_id": ObjectId(patient_id), "role": "patient"}, {"password": 0}
                        )
                    except:
                        pass
                
                if patient:
                    patient['_id'] = str(patient['_id'])
                    if 'user_id' in patient:
                        patient['user_id'] = str(patient['user_id'])
                    apt['patient'] = patient
                    
        return jsonify({"success": True, "appointments": appointments}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@doctor_bp.route('/appointments/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming():
    try:
        current_user = get_current_user()
        if not is_doctor(current_user):
            return jsonify({"success": False, "message": "Access denied"}), 403
        today = datetime.utcnow().strftime('%Y-%m-%d')
        appointments = list(db[COLLECTIONS['appointments']].find({
            "doctor_id": current_user['id'], "status": {"$in": ["pending", "confirmed"]},
            "appointment_date": {"$gte": today}
        }).sort("appointment_date", 1))
        
        for apt in appointments:
            apt['_id'] = str(apt['_id'])
            
            # Convert datetime objects to strings
            if 'created_at' in apt and hasattr(apt['created_at'], 'isoformat'):
                apt['created_at'] = apt['created_at'].isoformat()
            if 'updated_at' in apt and hasattr(apt['updated_at'], 'isoformat'):
                apt['updated_at'] = apt['updated_at'].isoformat()
            
            # Get patient details
            if apt.get('patient_id'):
                patient_id = apt['patient_id']
                patient = None
                
                try:
                    patient = db[COLLECTIONS['patients']].find_one(
                        {"user_id": ObjectId(patient_id)}, {"password": 0}
                    )
                except:
                    pass
                
                if not patient:
                    try:
                        patient = db[COLLECTIONS['users']].find_one(
                            {"_id": ObjectId(patient_id), "role": "patient"}, {"password": 0}
                        )
                    except:
                        pass
                
                if patient:
                    patient['_id'] = str(patient['_id'])
                    if 'user_id' in patient:
                        patient['user_id'] = str(patient['user_id'])
                    apt['patient'] = patient
                    
        return jsonify({"success": True, "appointments": appointments}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@doctor_bp.route('/update-status', methods=['PUT'])
@jwt_required()
def update_status():
    try:
        current_user = get_current_user()
        if not is_doctor(current_user):
            return jsonify({"success": False, "message": "Access denied"}), 403
        data = request.get_json()
        if not data.get('appointment_id') or not data.get('status'):
            return jsonify({"success": False, "message": "appointment_id and status required"}), 400
        update_data = {"status": data['status'], "updated_at": datetime.utcnow()}
        if data.get('doctor_notes'): update_data['doctor_notes'] = data['doctor_notes']
        if data.get('prescription'): update_data['prescription'] = data['prescription']
        result = db[COLLECTIONS['appointments']].update_one(
            {"_id": ObjectId(data['appointment_id']), "doctor_id": current_user['id']}, {"$set": update_data})
        if result.modified_count == 0:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        return jsonify({"success": True, "message": f"Status updated to {data['status']}"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@doctor_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        current_user = get_current_user()
        if not is_doctor(current_user):
            return jsonify({"success": False, "message": "Access denied"}), 403
        today = datetime.utcnow().strftime('%Y-%m-%d')
        stats = {
            "total": db[COLLECTIONS['appointments']].count_documents({"doctor_id": current_user['id']}),
            "today": db[COLLECTIONS['appointments']].count_documents({"doctor_id": current_user['id'], "appointment_date": today}),
            "pending": db[COLLECTIONS['appointments']].count_documents({"doctor_id": current_user['id'], "status": "pending"}),
            "completed": db[COLLECTIONS['appointments']].count_documents({"doctor_id": current_user['id'], "status": "completed"})
        }
        return jsonify({"success": True, "stats": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@doctor_bp.route('/availability', methods=['GET'])
@jwt_required()
def get_availability():
    """Get doctor's availability settings"""
    try:
        print("GET /availability endpoint called")
        current_user = get_current_user()
        print(f"Current user: {current_user}")
        
        if not is_doctor(current_user):
            print("Access denied - not a doctor")
            return jsonify({"success": False, "message": "Access denied"}), 403
        
        print(f"Looking for availability for doctor_id: {current_user['id']}")
        availability = db[COLLECTIONS['doctor_availability']].find_one({"doctor_id": current_user['id']})
        
        if availability:
            availability['_id'] = str(availability['_id'])
            if 'created_at' in availability and hasattr(availability['created_at'], 'isoformat'):
                availability['created_at'] = availability['created_at'].isoformat()
            if 'updated_at' in availability and hasattr(availability['updated_at'], 'isoformat'):
                availability['updated_at'] = availability['updated_at'].isoformat()
        else:
            # Return default availability
            availability = {
                "doctor_id": current_user['id'],
                "working_days": [0, 1, 2, 3, 4],  # Mon-Fri
                "time_ranges": [{"start": "09:00", "end": "17:00"}],
                "slot_duration": 30,
                "is_active": False
            }
        
        return jsonify({"success": True, "availability": availability}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@doctor_bp.route('/availability', methods=['POST'])
@jwt_required()
def set_availability():
    """Set or update doctor's availability settings"""
    try:
        print("POST /availability endpoint called")
        current_user = get_current_user()
        print(f"Current user: {current_user}")
        
        if not is_doctor(current_user):
            print("Access denied - not a doctor")
            return jsonify({"success": False, "message": "Access denied"}), 403
        
        data = request.get_json()
        print(f"Received data: {data}")
        
        # Validate required fields
        if 'working_days' not in data or 'time_ranges' not in data:
            return jsonify({"success": False, "message": "working_days and time_ranges are required"}), 400
        
        # Validate working_days (0-6)
        if not all(isinstance(day, int) and 0 <= day <= 6 for day in data['working_days']):
            return jsonify({"success": False, "message": "working_days must be integers between 0-6"}), 400
        
        # Validate time_ranges
        for time_range in data['time_ranges']:
            if 'start' not in time_range or 'end' not in time_range:
                return jsonify({"success": False, "message": "Each time_range must have start and end"}), 400
        
        availability_data = {
            "doctor_id": current_user['id'],
            "working_days": data['working_days'],
            "time_ranges": data['time_ranges'],
            "slot_duration": data.get('slot_duration', 30),
            "is_active": data.get('is_active', True),
            "updated_at": datetime.utcnow()
        }
        
        # Check if availability already exists
        existing = db[COLLECTIONS['doctor_availability']].find_one({"doctor_id": current_user['id']})
        
        if existing:
            # Update existing
            result = db[COLLECTIONS['doctor_availability']].update_one(
                {"doctor_id": current_user['id']},
                {"$set": availability_data}
            )
            message = "Availability updated successfully"
        else:
            # Create new
            availability_data['created_at'] = datetime.utcnow()
            result = db[COLLECTIONS['doctor_availability']].insert_one(availability_data)
            message = "Availability created successfully"
        
        return jsonify({"success": True, "message": message}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@doctor_bp.route('/available-slots/<doctor_id>/<date>', methods=['GET'])
def get_available_slots(doctor_id, date):
    """Get available time slots for a doctor on a specific date"""
    try:
        # Parse the date
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Get doctor's availability settings
        availability = db[COLLECTIONS['doctor_availability']].find_one({"doctor_id": doctor_id})
        
        if not availability or not availability.get('is_active'):
            return jsonify({"success": False, "message": "Doctor availability not configured"}), 404
        
        # Check if the requested day is a working day
        weekday = target_date.weekday()  # 0=Monday, 6=Sunday
        if weekday not in availability['working_days']:
            return jsonify({"success": True, "slots": [], "message": "Doctor is not available on this day"}), 200
        
        # Generate time slots based on time_ranges and slot_duration
        all_slots = []
        slot_duration = availability.get('slot_duration', 30)
        
        for time_range in availability['time_ranges']:
            start_time = datetime.strptime(time_range['start'], '%H:%M').time()
            end_time = datetime.strptime(time_range['end'], '%H:%M').time()
            
            current_time = datetime.combine(target_date, start_time)
            end_datetime = datetime.combine(target_date, end_time)
            
            while current_time < end_datetime:
                slot_time = current_time.strftime('%H:%M')
                all_slots.append(slot_time)
                current_time += timedelta(minutes=slot_duration)
        
        # Get booked appointments for this doctor on this date
        booked_appointments = list(db[COLLECTIONS['appointments']].find({
            "doctor_id": doctor_id,
            "appointment_date": date,
            "status": {"$in": ["pending", "confirmed"]}  # Only consider active appointments
        }))
        
        # Extract booked time slots
        booked_slots = [apt['appointment_time'] for apt in booked_appointments if 'appointment_time' in apt]
        
        # Filter out booked slots
        available_slots = [slot for slot in all_slots if slot not in booked_slots]
        
        # Don't show past slots for today
        if date == datetime.utcnow().strftime('%Y-%m-%d'):
            current_time_str = datetime.utcnow().strftime('%H:%M')
            available_slots = [slot for slot in available_slots if slot > current_time_str]
        
        return jsonify({
            "success": True,
            "date": date,
            "slots": available_slots,
            "slot_duration": slot_duration
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

