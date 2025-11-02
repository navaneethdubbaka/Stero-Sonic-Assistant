import React, { useRef, useEffect } from 'react';
import './ChatInterface.css';

function ChatInterface({ history }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  return (
    <div className="chat-interface">
      <h3>Chat with Stereo Sonic</h3>
      <div className="chat-messages">
        {history.length === 0 ? (
          <div className="empty-chat">
            <p>Start a conversation with Stereo Sonic!</p>
          </div>
        ) : (
          history.map((item, index) => (
            <div key={index} className={`chat-message ${item.type}`}>
              <div className="message-content">
                <div className="message-text">{item.text}</div>
                <div className="message-time">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

export default ChatInterface;

