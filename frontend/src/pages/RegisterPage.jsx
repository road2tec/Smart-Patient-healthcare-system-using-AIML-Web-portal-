import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaHeartbeat, FaEnvelope, FaLock, FaUser, FaPhone, FaSpinner, FaKey } from 'react-icons/fa';
import { toast } from 'react-toastify';
import axios from 'axios';
import { useAuth, API_URL } from '../App';
import './AuthPages.css';

const RegisterPage = () => {
    const [formData, setFormData] = useState({
        name: '', email: '', password: '', confirmPassword: '',
        phone: '', age: '', gender: '', blood_group: ''
    });
    const [loading, setLoading] = useState(false);
    const [otpSent, setOtpSent] = useState(false);
    const [otp, setOtp] = useState('');
    const [resendTimer, setResendTimer] = useState(0);
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    // Start countdown timer for resend OTP
    const startResendTimer = () => {
        setResendTimer(60);
        const timer = setInterval(() => {
            setResendTimer((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    };

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        if (!formData.name || !formData.email || !formData.password) {
            toast.error('Please fill in required fields');
            return;
        }
        if (formData.password !== formData.confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }
        if (formData.password.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/register/request-otp`, formData);
            if (response.data.success) {
                setOtpSent(true);
                startResendTimer();
                toast.success(response.data.message || 'OTP sent to your email!');
            }
        } catch (error) {
            toast.error(error.response?.data?.message || 'Failed to send OTP');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        if (!otp || otp.length !== 6) {
            toast.error('Please enter a valid 6-digit OTP');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/register/verify-otp`, {
                email: formData.email,
                otp: otp
            });
            if (response.data.success) {
                login(response.data.user, response.data.token);
                toast.success('Account created successfully! Email verified.');
                navigate('/patient');
            }
        } catch (error) {
            toast.error(error.response?.data?.message || 'OTP verification failed');
        } finally {
            setLoading(false);
        }
    };

    const handleResendOTP = async () => {
        if (resendTimer > 0) return;
        
        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/register/request-otp`, formData);
            if (response.data.success) {
                startResendTimer();
                toast.success('OTP resent to your email!');
                setOtp('');
            }
        } catch (error) {
            toast.error(error.response?.data?.message || 'Failed to resend OTP');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="auth-left">
                    <div className="auth-brand">
                        <Link to="/" className="logo">
                            <FaHeartbeat className="logo-icon" />
                            <span>SmartHealth</span>
                        </Link>
                    </div>
                    <div className="auth-illustration">
                        <div className="floating-card card-1">
                            <span>🏥</span>
                            <span>Healthcare</span>
                        </div>
                        <div className="floating-card card-2">
                            <span>🔬</span>
                            <span>AI Analysis</span>
                        </div>
                        <div className="floating-card card-3">
                            <span>💊</span>
                            <span>Treatment</span>
                        </div>
                    </div>
                    <h2>Patient Registration</h2>
                    <p>Create a patient account to access AI-powered healthcare services</p>
                </div>

                <div className="auth-right">
                    <div className="auth-form-container">
                        <h1>Patient Registration</h1>
                        <p className="auth-subtitle">
                            {otpSent 
                                ? 'Enter the OTP sent to your email' 
                                : 'Register as a patient to use symptom checker & book appointments'}
                        </p>

                        {otpSent && (
                            <div className="role-info-box" style={{backgroundColor: '#e8f5e9', borderColor: '#4caf50'}}>
                                <span className="role-badge" style={{backgroundColor: '#4caf50'}}>✉️ OTP Sent</span>
                                <p className="text-sm">Please check your email <strong>{formData.email}</strong> for the 6-digit OTP. The OTP is valid for 10 minutes.</p>
                            </div>
                        )}

                        {!otpSent && (
                            <div className="role-info-box">
                                <span className="role-badge">👤 Patient Account</span>
                                <p className="text-sm text-gray-500">Doctors are added by admin. If you're a doctor, please contact the administrator.</p>
                            </div>
                        )}

                        {!otpSent ? (
                            <form onSubmit={handleRequestOTP} className="auth-form">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Full Name *</label>
                                        <div className="input-with-icon">
                                            <FaUser className="input-icon" />
                                            <input type="text" name="name" className="form-input"
                                                placeholder="John Doe" value={formData.name} onChange={handleChange} />
                                        </div>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Phone Number</label>
                                        <div className="input-with-icon">
                                            <FaPhone className="input-icon" />
                                            <input type="tel" name="phone" className="form-input"
                                                placeholder="9876543210" value={formData.phone} onChange={handleChange} />
                                        </div>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Email Address *</label>
                                    <div className="input-with-icon">
                                        <FaEnvelope className="input-icon" />
                                        <input type="email" name="email" className="form-input"
                                            placeholder="john@example.com" value={formData.email} onChange={handleChange} />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Password *</label>
                                        <div className="input-with-icon">
                                            <FaLock className="input-icon" />
                                            <input type="password" name="password" className="form-input"
                                                placeholder="••••••••" value={formData.password} onChange={handleChange} />
                                        </div>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Confirm Password *</label>
                                        <div className="input-with-icon">
                                            <FaLock className="input-icon" />
                                            <input type="password" name="confirmPassword" className="form-input"
                                                placeholder="••••••••" value={formData.confirmPassword} onChange={handleChange} />
                                        </div>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Age</label>
                                        <input type="number" name="age" className="form-input"
                                            placeholder="25" value={formData.age} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Gender</label>
                                        <select name="gender" className="form-select" value={formData.gender} onChange={handleChange}>
                                            <option value="">Select</option>
                                            <option value="male">Male</option>
                                            <option value="female">Female</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Blood Group</label>
                                        <select name="blood_group" className="form-select" value={formData.blood_group} onChange={handleChange}>
                                            <option value="">Select</option>
                                            <option value="A+">A+</option>
                                            <option value="A-">A-</option>
                                            <option value="B+">B+</option>
                                            <option value="B-">B-</option>
                                            <option value="O+">O+</option>
                                            <option value="O-">O-</option>
                                            <option value="AB+">AB+</option>
                                            <option value="AB-">AB-</option>
                                        </select>
                                    </div>
                                </div>

                                <button type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
                                    {loading ? <><FaSpinner className="spin" /> Sending OTP...</> : 'Send OTP to Email'}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleVerifyOTP} className="auth-form">
                                <div className="form-group">
                                    <label className="form-label">Enter 6-Digit OTP *</label>
                                    <div className="input-with-icon">
                                        <FaKey className="input-icon" />
                                        <input 
                                            type="text" 
                                            className="form-input text-center text-2xl tracking-widest"
                                            placeholder="000000" 
                                            value={otp} 
                                            onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                            maxLength="6"
                                            style={{letterSpacing: '0.5rem', fontSize: '1.5rem', textAlign: 'center'}}
                                        />
                                    </div>
                                </div>

                                <button type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
                                    {loading ? <><FaSpinner className="spin" /> Verifying...</> : 'Verify OTP & Create Account'}
                                </button>

                                <div className="text-center mt-3">
                                    <button 
                                        type="button"
                                        onClick={handleResendOTP}
                                        disabled={resendTimer > 0 || loading}
                                        className="text-sm"
                                        style={{
                                            color: resendTimer > 0 ? '#999' : '#3b82f6',
                                            background: 'none',
                                            border: 'none',
                                            cursor: resendTimer > 0 ? 'not-allowed' : 'pointer',
                                            textDecoration: 'underline'
                                        }}
                                    >
                                        {resendTimer > 0 
                                            ? `Resend OTP in ${resendTimer}s` 
                                            : 'Resend OTP'}
                                    </button>
                                    <span className="mx-2">|</span>
                                    <button 
                                        type="button"
                                        onClick={() => {setOtpSent(false); setOtp(''); setResendTimer(0);}}
                                        className="text-sm"
                                        style={{
                                            color: '#ef4444',
                                            background: 'none',
                                            border: 'none',
                                            cursor: 'pointer',
                                            textDecoration: 'underline'
                                        }}
                                    >
                                        Change Email
                                    </button>
                                </div>
                            </form>
                        )}

                        <div className="auth-footer">
                            <p>Already have an account? <Link to="/login">Sign In</Link></p>
                            <p className="text-sm text-gray-500 mt-2">Are you a doctor? <Link to="/login">Login here</Link> (credentials from admin)</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RegisterPage;
