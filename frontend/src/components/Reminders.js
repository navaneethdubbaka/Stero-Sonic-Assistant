import React, { useState, useEffect } from 'react';
import './Reminders.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

function Reminders() {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCompleted, setShowCompleted] = useState(false);
  const [error, setError] = useState(null);

  const fetchReminders = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${API_BASE_URL}/api/reminders?include_completed=${showCompleted}`
      );
      const data = await response.json();
      
      if (data.success) {
        setReminders(data.reminders || []);
      } else {
        setError('Failed to load reminders');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error fetching reminders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchReminders, 30000);
    return () => clearInterval(interval);
  }, [showCompleted]);

  const handleToggleComplete = async (reminderId, currentStatus) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/reminders/${reminderId}/complete`,
        {
          method: 'PATCH'
        }
      );
      const data = await response.json();
      
      if (data.success) {
        fetchReminders();
      }
    } catch (err) {
      console.error('Error updating reminder:', err);
    }
  };

  const handleDelete = async (reminderId) => {
    if (!window.confirm('Are you sure you want to delete this reminder?')) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/reminders/${reminderId}`,
        {
          method: 'DELETE'
        }
      );
      const data = await response.json();
      
      if (data.success) {
        fetchReminders();
      }
    } catch (err) {
      console.error('Error deleting reminder:', err);
    }
  };

  const getPriorityClass = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'priority-high';
      case 'low':
        return 'priority-low';
      default:
        return 'priority-medium';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        // If not a valid date, return the string as is
        return dateString;
      }
      
      const now = new Date();
      const diff = date - now;
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      
      if (days < 0) {
        return `Overdue (${date.toLocaleDateString()})`;
      } else if (days === 0) {
        return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } else if (days === 1) {
        return 'Tomorrow';
      } else if (days < 7) {
        return `${days} days`;
      } else {
        return date.toLocaleDateString();
      }
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="reminders-container">
        <div className="loading">Loading reminders...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="reminders-container">
        <div className="error">{error}</div>
        <button onClick={fetchReminders} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="reminders-container">
      <div className="reminders-header">
        <h2>Reminders & Tasks</h2>
        <div className="reminders-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showCompleted}
              onChange={(e) => setShowCompleted(e.target.checked)}
            />
            Show completed
          </label>
          <button onClick={fetchReminders} className="refresh-btn">
            ↻ Refresh
          </button>
        </div>
      </div>

      {reminders.length === 0 ? (
        <div className="empty-state">
          <p>No reminders yet</p>
          <p className="hint">Say "Sonic, remind me to..." to create a reminder</p>
        </div>
      ) : (
        <div className="reminders-list">
          {reminders.map((reminder) => (
            <div
              key={reminder.id}
              className={`reminder-item ${reminder.completed ? 'completed' : ''} ${getPriorityClass(reminder.priority)}`}
            >
              <div className="reminder-checkbox">
                <input
                  type="checkbox"
                  checked={reminder.completed || false}
                  onChange={() => handleToggleComplete(reminder.id, reminder.completed)}
                />
              </div>
              
              <div className="reminder-content">
                <div className="reminder-title">{reminder.title}</div>
                {reminder.description && (
                  <div className="reminder-description">{reminder.description}</div>
                )}
                <div className="reminder-meta">
                  {reminder.due_date && (
                    <span className="reminder-due">
                      📅 {formatDate(reminder.due_date)}
                    </span>
                  )}
                  {reminder.priority && reminder.priority !== 'medium' && (
                    <span className={`reminder-priority ${getPriorityClass(reminder.priority)}`}>
                      {reminder.priority.toUpperCase()}
                    </span>
                  )}
                  <span className="reminder-created">
                    Created: {new Date(reminder.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              
              <button
                className="delete-btn"
                onClick={() => handleDelete(reminder.id)}
                title="Delete reminder"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Reminders;
