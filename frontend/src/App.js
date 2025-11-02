import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import VoiceInterface from './components/VoiceInterface';
import CommandHistory from './components/CommandHistory';
import StatusBar from './components/StatusBar';
import ReasoningDisplay from './components/ReasoningDisplay';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const WAKE_WORD = 'sonic';

function App() {
  const [listeningState, setListeningState] = useState('waiting'); // 'waiting', 'wake-word', 'command', 'processing'
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState({ message: 'Say "Sonic" to activate', type: 'info' });
  const [reasoning, setReasoning] = useState([]);
  const recognitionRef = useRef(null);
  const wakeWordDetectedRef = useRef(false);
  const isRecognitionRunningRef = useRef(false);
  const isInitializedRef = useRef(false);
  const listeningStateRef = useRef('waiting');

  // Helper function to safely start recognition
  const safeStartRecognition = () => {
    if (recognitionRef.current && !isRecognitionRunningRef.current) {
      try {
        recognitionRef.current.start();
        isRecognitionRunningRef.current = true;
      } catch (error) {
        if (error.name !== 'InvalidStateError') {
          console.error('Error starting recognition:', error);
        }
      }
    }
  };

  // Helper function to safely stop recognition
  const safeStopRecognition = () => {
    if (recognitionRef.current && isRecognitionRunningRef.current) {
      try {
        recognitionRef.current.stop();
        isRecognitionRunningRef.current = false;
      } catch (error) {
        console.error('Error stopping recognition:', error);
      }
    }
  };

  useEffect(() => {
    // Initialize Speech Recognition only once
    if (isInitializedRef.current) return;
    
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        isRecognitionRunningRef.current = true;
        if (!wakeWordDetectedRef.current) {
          listeningStateRef.current = 'wake-word';
          setListeningState('wake-word');
          setStatus({ message: 'Listening for "Sonic"...', type: 'info' });
        } else {
          listeningStateRef.current = 'command';
          setListeningState('command');
          setStatus({ message: 'Listening for your command...', type: 'listening' });
        }
      };

      recognition.onresult = async (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
        
        // Check for wake word if not detected yet
        if (!wakeWordDetectedRef.current) {
          if (transcript.includes(WAKE_WORD.toLowerCase())) {
            wakeWordDetectedRef.current = true;
            listeningStateRef.current = 'command';
            setListeningState('command');
            setStatus({ message: 'Sonic activated! What can I help you with?', type: 'listening' });
            speakText('Yes, I\'m listening');
            // Continue listening - recognition is already continuous, so it keeps going
          }
        } else {
          // Wake word already detected, this is the command
          wakeWordDetectedRef.current = false;
          listeningStateRef.current = 'processing';
          setListeningState('processing');
          // Don't stop recognition here - let it continue for next time
          await handleCommand(transcript);
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
          // Normal - just no speech detected, will continue
          return;
        }
        if (event.error === 'aborted') {
          // User stopped or we stopped it intentionally
          isRecognitionRunningRef.current = false;
          return;
        }
        if (event.error === 'network') {
          // Network error - try to restart
          isRecognitionRunningRef.current = false;
          wakeWordDetectedRef.current = false;
          listeningStateRef.current = 'waiting';
          setListeningState('waiting');
          setTimeout(() => safeStartRecognition(), 1000);
          return;
        }
        // Other errors
        isRecognitionRunningRef.current = false;
        setStatus({ message: `Error: ${event.error}`, type: 'error' });
        wakeWordDetectedRef.current = false;
        listeningStateRef.current = 'waiting';
        setListeningState('waiting');
        // Try to restart after error
        setTimeout(() => {
          if (!isRecognitionRunningRef.current && listeningStateRef.current === 'waiting') {
            safeStartRecognition();
          }
        }, 2000);
      };

      recognition.onend = () => {
        isRecognitionRunningRef.current = false;
        const currentState = listeningStateRef.current;
        
        // If we're processing, wait a bit longer and then restart
        if (currentState === 'processing') {
          // Wait for processing to finish, then restart
          setTimeout(() => {
            if (listeningStateRef.current === 'waiting' && !isRecognitionRunningRef.current) {
              wakeWordDetectedRef.current = false;
              safeStartRecognition();
            }
          }, 1500);
          return;
        }
        
        // Always restart after onend to maintain continuous listening
        setTimeout(() => {
          if (!isRecognitionRunningRef.current && listeningStateRef.current !== 'processing') {
            // Reset wake word detection if command state ended
            if (wakeWordDetectedRef.current) {
              wakeWordDetectedRef.current = false;
              listeningStateRef.current = 'waiting';
              setListeningState('waiting');
              setStatus({ message: 'Say "Sonic" to activate', type: 'info' });
            }
            safeStartRecognition();
          }
        }, 300);
      };

      recognitionRef.current = recognition;
      isInitializedRef.current = true;
      
      // Start listening for wake word after a short delay
      setTimeout(() => {
        safeStartRecognition();
      }, 500);
    } else {
      setStatus({ message: 'Speech recognition not available in this browser', type: 'error' });
    }

    return () => {
      safeStopRecognition();
    };
  }, []); // Empty dependency array - only initialize once

  const handleCommand = async (command) => {
    try {
      listeningStateRef.current = 'processing';
      setListeningState('processing');
      setStatus({ message: 'Processing...', type: 'info' });
      
      setHistory(prev => [...prev, { type: 'user', text: command, timestamp: new Date() }]);
      
      // Initialize reasoning display
      setReasoning(['💭 Analyzing your request...', '🤔 Determining which tools to use...']);
      
      // Always use chatbot API with tools enabled and reasoning
      const response = await fetch(`${API_BASE_URL}/api/chatbot/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: command,
          use_tools: true,
          return_reasoning: true
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update reasoning display with actual reasoning steps
        if (data.reasoning && data.reasoning.length > 0) {
          setReasoning(data.reasoning);
        }
        
        // Add final response
        if (data.tools_used && data.tools_used.length > 0) {
          setReasoning(prev => [...prev, '✅ Task completed successfully']);
        }
        
        setHistory(prev => [...prev, { 
          type: 'assistant', 
          text: data.response, 
          timestamp: new Date() 
        }]);
        speakText(data.response);
      } else {
        setReasoning(prev => [...prev, `❌ Error: ${data.error || 'Failed to process request'}`]);
        setHistory(prev => [...prev, { 
          type: 'error', 
          text: data.error || 'Failed to process request', 
          timestamp: new Date() 
        }]);
        speakText('Sorry, I encountered an error');
      }
    } catch (error) {
      console.error('Error:', error);
      setReasoning(prev => [...prev, `❌ Error: ${error.message}`]);
      setStatus({ message: `Error: ${error.message}`, type: 'error' });
      speakText('Sorry, I encountered an error');
    } finally {
      listeningStateRef.current = 'waiting';
      setListeningState('waiting');
      setStatus({ message: 'Say "Sonic" to activate', type: 'info' });
      wakeWordDetectedRef.current = false;
      
      // Clear reasoning after a delay
      setTimeout(() => {
        setReasoning([]);
      }, 5000);
      
      // Always restart recognition after processing to ensure continuous listening
      setTimeout(() => {
        if (!isRecognitionRunningRef.current && listeningStateRef.current === 'waiting') {
          safeStartRecognition();
        }
      }, 800);
    }
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      speechSynthesis.speak(utterance);
    }
  };

  const startListening = () => {
    wakeWordDetectedRef.current = false;
    safeStartRecognition();
  };

  const stopListening = () => {
    safeStopRecognition();
    wakeWordDetectedRef.current = false;
    listeningStateRef.current = 'waiting';
    setListeningState('waiting');
    setStatus({ message: 'Say "Sonic" to activate', type: 'info' });
  };

  const isListening = listeningState === 'wake-word' || listeningState === 'command';

  return (
    <div className="App">
      <div className="app-container">
        <StatusBar status={status} />
        
        <div className="main-content">
          <VoiceInterface
            isListening={isListening}
            listeningState={listeningState}
            onStartListening={startListening}
            onStopListening={stopListening}
          />
          
          <CommandHistory history={history} />
          
          <ReasoningDisplay 
            reasoning={reasoning} 
            isProcessing={listeningState === 'processing'} 
          />
        </div>
      </div>
    </div>
  );
}

export default App;

