import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { FaHeartbeat, FaStethoscope, FaCalendarAlt, FaHistory, FaSignOutAlt, FaUser, FaSearch, FaSpinner } from 'react-icons/fa';
import { toast } from 'react-toastify';
import axios from 'axios';
import { useAuth, API_URL } from '../App';
import './Dashboard.css';

// Symptom Checker Component
const SymptomChecker = () => {
    const [symptoms, setSymptoms] = useState('');
    const [loading, setLoading] = useState(false);
    const [prediction, setPrediction] = useState(null);
    const [doctors, setDoctors] = useState([]);
    const { getToken } = useAuth();

    const handlePredict = async (e) => {
        e.preventDefault();
        if (!symptoms.trim()) {
            toast.error('Please enter your symptoms');
            return;
        }
        setLoading(true);
        setPrediction(null);
        try {
            const response = await axios.post(`${API_URL}/symptoms/predict`,
                { symptoms },
                { headers: { Authorization: `Bearer ${getToken()}` } }
            );
            if (response.data.success) {
                setPrediction(response.data.prediction);
                setDoctors(response.data.available_doctors || []);
                toast.success('Prediction complete!');
            }
        } catch (error) {
            toast.error(error.response?.data?.message || 'Prediction failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-content animate-fadeIn">
            <div className="page-header">
                <h1><FaStethoscope /> AI Symptom Checker</h1>
                <p>Enter your symptoms to get AI-powered disease prediction</p>
            </div>

            <div className="symptom-section">
                <div className="card symptom-input-card">
                    <h3>Describe Your Symptoms</h3>
                    <p className="text-gray-500 mb-4">Enter symptoms separated by commas (e.g., headache, fever, cough)</p>
                    <form onSubmit={handlePredict}>
                        <textarea
                            className="form-input"
                            placeholder="e.g., itching, skin rash, fatigue, high fever, headache..."
                            value={symptoms}
                            onChange={(e) => setSymptoms(e.target.value)}
                            rows={4}
                        />
                        <button type="submit" className="btn btn-primary btn-lg mt-4" disabled={loading}>
                            {loading ? <><FaSpinner className="spin" /> Analyzing...</> : <><FaSearch /> Analyze Symptoms</>}
                        </button>
                    </form>
                </div>

                {prediction && (
                    <div className="prediction-results animate-fadeIn">
                        <div className="card prediction-card">
                            <div className="prediction-header">
                                <div className="prediction-icon">🎯</div>
                                <div>
                                    <h3>Prediction Result</h3>
                                    <p className="text-gray-500">Based on AI analysis</p>
                                </div>
                            </div>
                            <div className="prediction-main">
                                <div className="disease-name">{prediction.disease}</div>
                                <div className="confidence-bar">
                                    <div className="confidence-fill" style={{ width: `${prediction.confidence}%` }}></div>
                                </div>
                                <div className="confidence-text">{prediction.confidence}% Confidence</div>
                            </div>
                            <div className="specialization-badge">
                                <span>Recommended Specialist:</span>
                                <strong>{prediction.specialization}</strong>
                            </div>
                        </div>

                        {prediction.top_predictions && (
                            <div className="card">
                                <h3>Other Possible Conditions</h3>
                                <div className="other-predictions">
                                    {prediction.top_predictions.slice(1).map((p, i) => (
                                        <div key={i} className="other-pred-item">
                                            <span>{p.disease}</span>
                                            <span className="badge badge-primary">{p.probability}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {doctors.length > 0 ? (
                            <div className="card">
                                <h3>Recommended {prediction.specialization} Specialists</h3>
                                <p className="text-gray-500 mb-4">
                                    Based on your symptoms, we recommend consulting with these {prediction.specialization} specialists
                                </p>
                                <div className="doctors-list">
                                    {doctors.map((doc, i) => (
                                        <DoctorCard key={i} doctor={doc} prediction={prediction} />
                                    ))}
                                </div>
                            </div>
                        ) : prediction && (
                            <div className="card">
                                <div className="no-doctors-message">
                                    <h3>No {prediction.specialization} Specialists Available</h3>
                                    <p>Currently, there are no {prediction.specialization} doctors available for booking. 
                                    Please contact our reception or try again later.</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

// Doctor Card Component
const DoctorCard = ({ doctor, prediction }) => {
    const navigate = useNavigate();
    return (
        <div className="doctor-card">
            {prediction && (
                <div className="recommended-badge">
                    ✓ Recommended Specialist
                </div>
            )}
            <div className="doctor-avatar">
                <FaUser />
            </div>
            <div className="doctor-info">
                <h4>Dr. {doctor.name}</h4>
                <p className="specialization">
                    <strong>{doctor.specialization}</strong>
                </p>
                <p className="experience">{doctor.experience || 'Experienced'}</p>
                {doctor.consultation_fee && (
                    <p className="fee">₹{doctor.consultation_fee} consultation</p>
                )}
                {prediction && (
                    <p className="match-info">
                        Specializes in treating {prediction.disease}
                    </p>
                )}
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => navigate(`/patient/book/${doctor._id}`)}>
                Book Appointment
            </button>
        </div>
    );
};

// Appointments Component
const MyAppointments = () => {
    const [appointments, setAppointments] = useState([]);
    const [loading, setLoading] = useState(true);
    const { getToken } = useAuth();

    useEffect(() => {
        fetchAppointments();
    }, []);

    const fetchAppointments = async () => {
        try {
            const response = await axios.get(`${API_URL}/appointments/my`,
                { headers: { Authorization: `Bearer ${getToken()}` } }
            );
            if (response.data.success) {
                setAppointments(response.data.appointments);
            }
        } catch (error) {
            toast.error('Failed to fetch appointments');
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        const classes = {
            pending: 'badge-warning',
            confirmed: 'badge-primary',
            completed: 'badge-success',
            cancelled: 'badge-error'
        };
        return <span className={`badge ${classes[status]}`}>{status}</span>;
    };

    if (loading) return <div className="loading-overlay"><div className="spinner"></div></div>;

    return (
        <div className="page-content animate-fadeIn">
            <div className="page-header">
                <h1><FaCalendarAlt /> My Appointments</h1>
                <p>View and manage your appointments</p>
            </div>

            {appointments.length === 0 ? (
                <div className="empty-state card">
                    <FaCalendarAlt className="empty-icon" />
                    <h3>No Appointments Yet</h3>
                    <p>Use the symptom checker to get recommendations and book an appointment</p>
                    <Link to="/patient" className="btn btn-primary">Check Symptoms</Link>
                </div>
            ) : (
                <div className="appointments-grid">
                    {appointments.map((apt) => (
                        <div key={apt._id} className="card appointment-card">
                            <div className="apt-header">
                                <div className="apt-date">
                                    <span className="date">{apt.appointment_date}</span>
                                    <span className="time">{apt.appointment_time}</span>
                                </div>
                                {getStatusBadge(apt.status)}
                            </div>
                            <div className="apt-body">
                                {apt.doctor && (
                                    <div className="apt-doctor">
                                        <FaUser className="doc-icon" />
                                        <div>
                                            <h4>Dr. {apt.doctor.name}</h4>
                                            <p>{apt.doctor.specialization}</p>
                                        </div>
                                    </div>
                                )}
                                {apt.predicted_disease && (
                                    <div className="apt-disease">
                                        <span>Predicted Condition:</span>
                                        <strong>{apt.predicted_disease}</strong>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// Book Appointment Component
const BookAppointment = () => {
    const [doctors, setDoctors] = useState([]);
    const [selectedDoctor, setSelectedDoctor] = useState(null);
    const [date, setDate] = useState('');
    const [time, setTime] = useState('');
    const [availableSlots, setAvailableSlots] = useState([]);
    const [loadingSlots, setLoadingSlots] = useState(false);
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);
    const { getToken } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchDoctors();
    }, []);

    useEffect(() => {
        if (selectedDoctor && date) {
            fetchAvailableSlots();
        } else {
            setAvailableSlots([]);
            setTime('');
        }
    }, [selectedDoctor, date]);

    const fetchDoctors = async () => {
        try {
            const response = await axios.get(`${API_URL}/doctors`,
                { headers: { Authorization: `Bearer ${getToken()}` } }
            );
            if (response.data.success) {
                setDoctors(response.data.doctors);
            }
        } catch (error) {
            console.error('Failed to fetch doctors');
        }
    };

    const fetchAvailableSlots = async () => {
        setLoadingSlots(true);
        setTime('');
        try {
            const response = await axios.get(
                `${API_URL}/doctor/available-slots/${selectedDoctor}/${date}`
            );
            if (response.data.success) {
                setAvailableSlots(response.data.slots || []);
                if (response.data.slots.length === 0) {
                    toast.info('No available slots for this date');
                }
            }
        } catch (error) {
            console.error('Failed to fetch slots:', error);
            setAvailableSlots([]);
            toast.error(error.response?.data?.message || 'Failed to load available slots');
        } finally {
            setLoadingSlots(false);
        }
    };

    const handleBook = async (e) => {
        e.preventDefault();
        if (!selectedDoctor || !date || !time) {
            toast.error('Please fill all required fields');
            return;
        }
        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/appointments/book`,
                { doctor_id: selectedDoctor, appointment_date: date, appointment_time: time, notes },
                { headers: { Authorization: `Bearer ${getToken()}` } }
            );
            if (response.data.success) {
                toast.success('Appointment booked successfully!');
                navigate('/patient/appointments');
            }
        } catch (error) {
            toast.error(error.response?.data?.message || 'Booking failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-content animate-fadeIn">
            <div className="page-header">
                <h1><FaCalendarAlt /> Book Appointment</h1>
                <p>Schedule an appointment with a doctor</p>
            </div>

            <div className="card booking-form">
                <form onSubmit={handleBook}>
                    <div className="form-group">
                        <label className="form-label">Select Doctor *</label>
                        <select 
                            className="form-select" 
                            value={selectedDoctor || ''} 
                            onChange={(e) => {
                                setSelectedDoctor(e.target.value);
                                setTime('');
                            }}
                        >
                            <option value="">Choose a doctor</option>
                            {doctors.map((doc) => (
                                <option key={doc._id} value={doc._id}>
                                    Dr. {doc.name} - {doc.specialization}
                                </option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Date *</label>
                            <input 
                                type="date" 
                                className="form-input" 
                                value={date} 
                                onChange={(e) => {
                                    setDate(e.target.value);
                                    setTime('');
                                }} 
                                min={new Date().toISOString().split('T')[0]}
                                disabled={!selectedDoctor}
                            />
                            {!selectedDoctor && (
                                <p className="help-text">Please select a doctor first</p>
                            )}
                        </div>
                    </div>

                    {selectedDoctor && date && (
                        <div className="form-group">
                            <label className="form-label">Available Time Slots *</label>
                            {loadingSlots ? (
                                <div className="slots-loading">
                                    <FaSpinner className="spin" /> Loading available slots...
                                </div>
                            ) : availableSlots.length > 0 ? (
                                <div className="time-slots-grid">
                                    {availableSlots.map((slot) => (
                                        <button
                                            key={slot}
                                            type="button"
                                            className={`time-slot ${time === slot ? 'selected' : ''}`}
                                            onClick={() => setTime(slot)}
                                        >
                                            {slot}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="no-slots-message">
                                    <p>No available slots for this date. Please select another date.</p>
                                </div>
                            )}
                        </div>
                    )}
                    
                    <div className="form-group">
                        <label className="form-label">Notes (Optional)</label>
                        <textarea 
                            className="form-input" 
                            placeholder="Any additional notes..." 
                            value={notes} 
                            onChange={(e) => setNotes(e.target.value)} 
                            rows={3} 
                        />
                    </div>
                    <button type="submit" className="btn btn-primary btn-lg" disabled={loading || !time}>
                        {loading ? <><FaSpinner className="spin" /> Booking...</> : 'Book Appointment'}
                    </button>
                </form>
            </div>

            <style jsx>{`
                .time-slots-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                    gap: 10px;
                    margin-top: 10px;
                }

                .time-slot {
                    padding: 12px 16px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    background: white;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-weight: 500;
                }

                .time-slot:hover {
                    border-color: #4CAF50;
                    background-color: #f5f5f5;
                }

                .time-slot.selected {
                    border-color: #4CAF50;
                    background-color: #4CAF50;
                    color: white;
                }

                .slots-loading {
                    padding: 20px;
                    text-align: center;
                    color: #666;
                }

                .no-slots-message {
                    padding: 20px;
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 8px;
                    color: #856404;
                }

                .help-text {
                    font-size: 14px;
                    color: #666;
                    margin-top: 5px;
                }
            `}</style>
        </div>
    );
};

// Main Patient Dashboard
const PatientDashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <div className="dashboard">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <FaHeartbeat className="sidebar-logo" />
                    <span>SmartHealth</span>
                </div>
                <nav className="sidebar-nav">
                    <Link to="/patient" className="nav-item"><FaStethoscope /> Symptom Checker</Link>
                    <Link to="/patient/appointments" className="nav-item"><FaCalendarAlt /> My Appointments</Link>
                    <Link to="/patient/book" className="nav-item"><FaHistory /> Book Appointment</Link>
                </nav>
                <div className="sidebar-footer">
                    <div className="user-info">
                        <FaUser className="user-avatar" />
                        <div>
                            <span className="user-name">{user?.name}</span>
                            <span className="user-role">Patient</span>
                        </div>
                    </div>
                    <button onClick={handleLogout} className="logout-btn"><FaSignOutAlt /> Logout</button>
                </div>
            </aside>

            <main className="main-content">
                <Routes>
                    <Route path="/" element={<SymptomChecker />} />
                    <Route path="/appointments" element={<MyAppointments />} />
                    <Route path="/book" element={<BookAppointment />} />
                    <Route path="/book/:doctorId" element={<BookAppointment />} />
                </Routes>
            </main>
        </div>
    );
};

export default PatientDashboard;
