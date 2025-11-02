import React from 'react';
import './CommandHistory.css';

function CommandHistory({ history }) {
  return (
    <div className="command-history">
      <h3>Command History</h3>
      <div className="history-list">
        {history.length === 0 ? (
          <div className="empty-history">
            <p>No commands yet. Start speaking to see your command history.</p>
          </div>
        ) : (
          history.map((item, index) => (
            <div key={index} className={`history-item ${item.type}`}>
              <div className="history-header">
                <span className="history-type">{item.type}</span>
                <span className="history-time">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="history-text">{item.text}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default CommandHistory;

