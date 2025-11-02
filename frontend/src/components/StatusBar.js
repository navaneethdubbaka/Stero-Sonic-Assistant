import React from 'react';
import './StatusBar.css';

function StatusBar({ status }) {
  return (
    <div className="status-bar">
      <div className="status-indicator">
        <div className={`status-dot ${status.type}`}></div>
        <span className="status-message">{status.message}</span>
      </div>
      <div className="status-meta">
        <span className="status-mode">Stereo Sonic Assistant</span>
      </div>
    </div>
  );
}

export default StatusBar;

