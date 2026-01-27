import React, { useState, useEffect } from 'react';
import { useAuth, API_URL } from '../App';
import './Dashboard.css';

const DoctorAvailability = () => {
  const { getToken } = useAuth();
  const [availability, setAvailability] = useState({
    working_days: [0, 1, 2, 3, 4], // Mon-Fri by default
    time_ranges: [{ start: '09:00', end: '17:00' }],
    slot_duration: 30,
    is_active: false
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const daysOfWeek = [
    { value: 0, label: 'Monday' },
    { value: 1, label: 'Tuesday' },
    { value: 2, label: 'Wednesday' },
    { value: 3, label: 'Thursday' },
    { value: 4, label: 'Friday' },
    { value: 5, label: 'Saturday' },
    { value: 6, label: 'Sunday' }
  ];

  const slotDurations = [15, 20, 30, 45, 60];

  useEffect(() => {
    fetchAvailability();
  }, []);

  const fetchAvailability = async () => {
    try {
      const token = getToken();
      if (!token) {
        setMessage({ type: 'error', text: 'Please login again - session expired' });
        setLoading(false);
        return;
      }
      
      console.log('Fetching availability from:', `${API_URL}/doctor/availability`);
      console.log('Token:', token ? 'Present' : 'Missing');
      
      const response = await fetch(`${API_URL}/doctor/availability`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Server error' }));
        console.error('Error response:', errorData);
        setMessage({ type: 'error', text: errorData.message || `Server error: ${response.status}` });
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.success && data.availability) {
        setAvailability(data.availability);
      } else if (!data.success) {
        setMessage({ type: 'error', text: data.message || 'Failed to load availability settings' });
      }
    } catch (error) {
      console.error('Error fetching availability:', error);
      setMessage({ type: 'error', text: `Network error: ${error.message}. Make sure backend is running.` });
    } finally {
      setLoading(false);
    }
  };

  const handleDayToggle = (dayValue) => {
    setAvailability(prev => {
      const working_days = prev.working_days.includes(dayValue)
        ? prev.working_days.filter(d => d !== dayValue)
        : [...prev.working_days, dayValue].sort((a, b) => a - b);
      return { ...prev, working_days };
    });
  };

  const handleTimeRangeChange = (index, field, value) => {
    setAvailability(prev => {
      const time_ranges = [...prev.time_ranges];
      time_ranges[index] = { ...time_ranges[index], [field]: value };
      return { ...prev, time_ranges };
    });
  };

  const addTimeRange = () => {
    setAvailability(prev => ({
      ...prev,
      time_ranges: [...prev.time_ranges, { start: '09:00', end: '17:00' }]
    }));
  };

  const removeTimeRange = (index) => {
    if (availability.time_ranges.length > 1) {
      setAvailability(prev => ({
        ...prev,
        time_ranges: prev.time_ranges.filter((_, i) => i !== index)
      }));
    }
  };

  const handleSave = async () => {
    if (availability.working_days.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one working day' });
      return;
    }

    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const token = getToken();
      if (!token) {
        setMessage({ type: 'error', text: 'Please login again - session expired' });
        setSaving(false);
        return;
      }
      
      console.log('Saving availability to:', `${API_URL}/doctor/availability`);
      console.log('Token:', token ? 'Present' : 'Missing');
      console.log('Availability data:', availability);
      
      const response = await fetch(`${API_URL}/doctor/availability`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(availability)
      });

      console.log('Save response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Server error' }));
        console.error('Error response:', errorData);
        setMessage({ type: 'error', text: errorData.message || `Server error: ${response.status}` });
        setSaving(false);
        return;
      }
      
      const data = await response.json();
      console.log('Save response data:', data);
      
      if (data.success) {
        setMessage({ type: 'success', text: data.message || 'Availability saved successfully!' });
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      } else {
        setMessage({ type: 'error', text: data.message || 'Failed to save availability' });
      }
    } catch (error) {
      console.error('Error saving availability:', error);
      setMessage({ type: 'error', text: `Network error: ${error.message}. Make sure backend server is running on port 5000.` });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading availability settings...</div>;
  }

  return (
    <div className="availability-container">
      <h2>Manage Your Availability</h2>
      <p className="subtitle">Set your working hours and appointment slot duration</p>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="availability-section">
        <h3>Working Days</h3>
        <div className="days-grid">
          {daysOfWeek.map(day => (
            <label key={day.value} className="day-checkbox">
              <input
                type="checkbox"
                checked={availability.working_days.includes(day.value)}
                onChange={() => handleDayToggle(day.value)}
              />
              <span>{day.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="availability-section">
        <h3>Working Hours</h3>
        {availability.time_ranges.map((range, index) => (
          <div key={index} className="time-range">
            <div className="time-inputs">
              <div className="time-input-group">
                <label>Start Time</label>
                <input
                  type="time"
                  value={range.start}
                  onChange={(e) => handleTimeRangeChange(index, 'start', e.target.value)}
                />
              </div>
              <div className="time-input-group">
                <label>End Time</label>
                <input
                  type="time"
                  value={range.end}
                  onChange={(e) => handleTimeRangeChange(index, 'end', e.target.value)}
                />
              </div>
              {availability.time_ranges.length > 1 && (
                <button
                  type="button"
                  className="remove-btn"
                  onClick={() => removeTimeRange(index)}
                >
                  Remove
                </button>
              )}
            </div>
          </div>
        ))}
        <button type="button" className="add-time-range-btn" onClick={addTimeRange}>
          + Add Time Range
        </button>
      </div>

      <div className="availability-section">
        <h3>Appointment Slot Duration</h3>
        <div className="slot-duration">
          {slotDurations.map(duration => (
            <label key={duration} className="duration-option">
              <input
                type="radio"
                name="slot_duration"
                value={duration}
                checked={availability.slot_duration === duration}
                onChange={(e) => setAvailability(prev => ({
                  ...prev,
                  slot_duration: parseInt(e.target.value)
                }))}
              />
              <span>{duration} minutes</span>
            </label>
          ))}
        </div>
      </div>

      <div className="availability-section">
        <label className="active-toggle">
          <input
            type="checkbox"
            checked={availability.is_active}
            onChange={(e) => setAvailability(prev => ({
              ...prev,
              is_active: e.target.checked
            }))}
          />
          <span>Enable Online Booking</span>
        </label>
        <p className="help-text">
          When enabled, patients can book appointments based on your availability
        </p>
      </div>

      <div className="actions">
        <button
          className="save-btn"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Availability'}
        </button>
      </div>

      <style jsx>{`
        .availability-container {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }

        .subtitle {
          color: #666;
          margin-bottom: 30px;
        }

        .message {
          padding: 12px 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-weight: 500;
        }

        .message.success {
          background-color: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }

        .message.error {
          background-color: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }

        .availability-section {
          background: white;
          padding: 25px;
          border-radius: 12px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .availability-section h3 {
          margin-top: 0;
          margin-bottom: 20px;
          color: #333;
        }

        .days-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 12px;
        }

        .day-checkbox {
          display: flex;
          align-items: center;
          padding: 10px;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .day-checkbox:hover {
          border-color: #4CAF50;
          background-color: #f5f5f5;
        }

        .day-checkbox input[type="checkbox"] {
          margin-right: 8px;
        }

        .day-checkbox input[type="checkbox"]:checked + span {
          font-weight: 600;
          color: #4CAF50;
        }

        .time-range {
          margin-bottom: 15px;
        }

        .time-inputs {
          display: flex;
          gap: 15px;
          align-items: flex-end;
        }

        .time-input-group {
          flex: 1;
        }

        .time-input-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
          color: #555;
        }

        .time-input-group input[type="time"] {
          width: 100%;
          padding: 10px;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          font-size: 16px;
        }

        .remove-btn {
          padding: 10px 20px;
          background-color: #f44336;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }

        .remove-btn:hover {
          background-color: #d32f2f;
        }

        .add-time-range-btn {
          padding: 10px 20px;
          background-color: #2196F3;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }

        .add-time-range-btn:hover {
          background-color: #1976D2;
        }

        .slot-duration {
          display: flex;
          gap: 15px;
          flex-wrap: wrap;
        }

        .duration-option {
          display: flex;
          align-items: center;
          padding: 10px 15px;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .duration-option:hover {
          border-color: #4CAF50;
          background-color: #f5f5f5;
        }

        .duration-option input[type="radio"] {
          margin-right: 8px;
        }

        .duration-option input[type="radio"]:checked + span {
          font-weight: 600;
          color: #4CAF50;
        }

        .active-toggle {
          display: flex;
          align-items: center;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
        }

        .active-toggle input[type="checkbox"] {
          margin-right: 10px;
          width: 20px;
          height: 20px;
          cursor: pointer;
        }

        .help-text {
          color: #666;
          font-size: 14px;
          margin-top: 8px;
          margin-left: 30px;
        }

        .actions {
          text-align: center;
          margin-top: 30px;
        }

        .save-btn {
          padding: 14px 40px;
          background-color: #4CAF50;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .save-btn:hover:not(:disabled) {
          background-color: #45a049;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        }

        .save-btn:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .loading {
          text-align: center;
          padding: 40px;
          font-size: 18px;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default DoctorAvailability;
