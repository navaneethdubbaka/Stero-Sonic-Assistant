import React from 'react';
import './VoiceInterface.css';

function VoiceInterface({ isListening, listeningState, onStartListening, onStopListening }) {
  const getStatusText = () => {
    switch (listeningState) {
      case 'wake-word':
        return 'Listening for "Sonic"...';
      case 'command':
        return 'Listening for your command...';
      case 'processing':
        return 'Processing your request...';
      default:
        return 'Say "Sonic" to activate';
    }
  };

  const getIcon = () => {
    if (listeningState === 'processing') {
      return (
        <div className="processing-icon">
          <div className="spinner"></div>
        </div>
      );
    } else if (isListening) {
      return <div className="pulse-ring"></div>;
    } else {
      return (
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      );
    }
  };

  return (
    <div className="voice-interface">
      <div className="voice-controls">
        <div className={`voice-button-container ${isListening ? 'listening' : ''} ${listeningState === 'processing' ? 'processing' : ''}`}>
          <button
            className="voice-button"
            onClick={listeningState === 'processing' ? null : (isListening ? onStopListening : onStartListening)}
            disabled={listeningState === 'processing'}
            aria-label={isListening ? 'Stop listening' : 'Start listening'}
          >
            <div className="voice-icon">
              {getIcon()}
            </div>
          </button>
          <p className="voice-status">{getStatusText()}</p>
        </div>
      </div>
      
      <div className="wake-word-info">
        <p>Say <strong>"Sonic"</strong> to activate, then tell me what you need</p>
        <p className="help-text">I can help with emails, WhatsApp, searches, camera, and more!</p>
      </div>
    </div>
  );
}

export default VoiceInterface;

