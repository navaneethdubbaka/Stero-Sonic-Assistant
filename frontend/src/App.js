import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import VoiceInterface from './components/VoiceInterface';
import CommandHistory from './components/CommandHistory';
import StatusBar from './components/StatusBar';
import ReasoningDisplay from './components/ReasoningDisplay';
import Reminders from './components/Reminders';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const WAKE_WORD = 'sonic';
// Buffer after stopping recognition so the mic can restart reliably (Chrome/WebView often needs >300ms).
const LISTEN_START_DELAY_MS = 850;
// With beep-only activation we do not skip the first transcript (skipping was for old TTS echo and could drop the user's command).
const SKIP_FIRST_TRANSCRIPT = false;

function playActivationBeep() {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    if (ctx.state === 'suspended') {
      ctx.resume();
    }
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    const t0 = ctx.currentTime;
    gain.gain.setValueAtTime(0, t0);
    gain.gain.linearRampToValueAtTime(0.12, t0 + 0.05);
    gain.gain.linearRampToValueAtTime(0, t0 + 0.18);
    osc.start(t0);
    osc.stop(t0 + 0.2);
    osc.onended = () => {
      try {
        ctx.close();
      } catch (_e) {
        /* ignore */
      }
    };
  } catch (e) {
    console.warn('Activation beep failed:', e);
  }
}

function speakText(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
  }
}

function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'reminders'
  const [listeningState, setListeningState] = useState('waiting'); // 'waiting', 'wake-word', 'command', 'processing'
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState({ message: 'Say "Sonic" to activate', type: 'info' });
  const [reasoning, setReasoning] = useState([]);
  const recognitionRef = useRef(null);
  const wakeWordDetectedRef = useRef(false);
  const readyForCommandRef = useRef(false);
  const skipNextTranscriptRef = useRef(false); // Skip first transcript after we start listening (avoids echo)
  const stoppedForTtsRef = useRef(false);
  const isRecognitionRunningRef = useRef(false);
  const isInitializedRef = useRef(false);
  const listeningStateRef = useRef('waiting');
  const commandSessionRef = useRef(0);
  const chatAbortRef = useRef(null);
  const handleCommandRef = useRef(async () => {});

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

  const scheduleActivationListen = useCallback(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    stoppedForTtsRef.current = true;
    safeStopRecognition();
    playActivationBeep();
    setTimeout(() => {
      stoppedForTtsRef.current = false;
      readyForCommandRef.current = true;
      safeStartRecognition();
      // Chrome/WebView: start() right after stop() often needs a retry.
      setTimeout(() => {
        if (!isRecognitionRunningRef.current) {
          safeStartRecognition();
        }
      }, 200);
      setTimeout(() => {
        if (!isRecognitionRunningRef.current) {
          safeStartRecognition();
        }
      }, 500);
    }, LISTEN_START_DELAY_MS);
  }, []);

  const handleCommand = useCallback(async (command, sessionId) => {
    const controller = new AbortController();
    chatAbortRef.current = controller;
    const signal = controller.signal;

    try {
      listeningStateRef.current = 'processing';
      setListeningState('processing');
      setStatus({ message: 'Processing...', type: 'info' });

      setHistory(prev => [...prev, { type: 'user', text: command, timestamp: new Date() }]);

      setReasoning(['💭 Analyzing your request...', '🤔 Determining which tools to use...']);

      const response = await fetch(`${API_BASE_URL}/api/chatbot/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: command,
          use_tools: true,
          return_reasoning: true,
        }),
        signal,
      });

      if (sessionId !== commandSessionRef.current) {
        return;
      }

      const data = await response.json();

      if (sessionId !== commandSessionRef.current) {
        return;
      }

      if (data.success) {
        if (data.reasoning && data.reasoning.length > 0) {
          setReasoning(data.reasoning);
        }

        if (data.tools_used && data.tools_used.length > 0) {
          setReasoning(prev => [...prev, '✅ Task completed successfully']);
        }

        setHistory(prev => [
          ...prev,
          {
            type: 'assistant',
            text: data.response,
            timestamp: new Date(),
          },
        ]);
        speakText(data.response);
      } else {
        setReasoning(prev => [...prev, `❌ Error: ${data.error || 'Failed to process request'}`]);
        setHistory(prev => [
          ...prev,
          {
            type: 'error',
            text: data.error || 'Failed to process request',
            timestamp: new Date(),
          },
        ]);
        speakText('Sorry, I encountered an error');
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        return;
      }
      console.error('Error:', error);
      if (sessionId !== commandSessionRef.current) {
        return;
      }
      setReasoning(prev => [...prev, `❌ Error: ${error.message}`]);
      setStatus({ message: `Error: ${error.message}`, type: 'error' });
      speakText('Sorry, I encountered an error');
    } finally {
      if (sessionId !== commandSessionRef.current) {
        return;
      }
      chatAbortRef.current = null;

      listeningStateRef.current = 'waiting';
      setListeningState('waiting');
      setStatus({ message: 'Say "Sonic" to activate', type: 'info' });
      wakeWordDetectedRef.current = false;

      setTimeout(() => {
        setReasoning([]);
      }, 5000);

      setTimeout(() => {
        if (!isRecognitionRunningRef.current && listeningStateRef.current === 'waiting') {
          safeStartRecognition();
        }
      }, 800);
    }
  }, []);

  handleCommandRef.current = handleCommand;

  useEffect(() => {
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

        // Barge-in: stop TTS + abort request, then same flow as fresh activation (beep → command mode)
        if (
          listeningStateRef.current === 'processing' &&
          transcript.includes(WAKE_WORD.toLowerCase())
        ) {
          window.speechSynthesis.cancel();
          try {
            chatAbortRef.current?.abort();
          } catch (_e) {
            /* ignore */
          }
          commandSessionRef.current += 1;
          setReasoning([]);

          wakeWordDetectedRef.current = true;
          readyForCommandRef.current = false;
          skipNextTranscriptRef.current = SKIP_FIRST_TRANSCRIPT;
          listeningStateRef.current = 'command';
          setListeningState('command');
          setStatus({ message: 'Sonic activated! What can I help you with?', type: 'listening' });
          scheduleActivationListen();
          return;
        }

        if (!wakeWordDetectedRef.current) {
          if (transcript.includes(WAKE_WORD.toLowerCase())) {
            wakeWordDetectedRef.current = true;
            readyForCommandRef.current = false;
            skipNextTranscriptRef.current = SKIP_FIRST_TRANSCRIPT;
            listeningStateRef.current = 'command';
            setListeningState('command');
            setStatus({ message: 'Sonic activated! What can I help you with?', type: 'listening' });
            scheduleActivationListen();
          }
        } else {
          if (!readyForCommandRef.current) {
            return;
          }
          if (skipNextTranscriptRef.current) {
            skipNextTranscriptRef.current = false;
            return;
          }
          const t = transcript.replace(/[',.]/g, '').trim();
          const isSonic = t === 'sonic' || t === 'sonics';
          if (isSonic) {
            return;
          }
          wakeWordDetectedRef.current = false;
          readyForCommandRef.current = false;
          listeningStateRef.current = 'processing';
          setListeningState('processing');
          commandSessionRef.current += 1;
          const sessionId = commandSessionRef.current;
          await handleCommandRef.current(transcript, sessionId);
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
          return;
        }
        if (event.error === 'aborted') {
          isRecognitionRunningRef.current = false;
          return;
        }
        if (event.error === 'network') {
          isRecognitionRunningRef.current = false;
          wakeWordDetectedRef.current = false;
          listeningStateRef.current = 'waiting';
          setListeningState('waiting');
          setTimeout(() => safeStartRecognition(), 1000);
          return;
        }
        isRecognitionRunningRef.current = false;
        setStatus({ message: `Error: ${event.error}`, type: 'error' });
        wakeWordDetectedRef.current = false;
        listeningStateRef.current = 'waiting';
        setListeningState('waiting');
        setTimeout(() => {
          if (!isRecognitionRunningRef.current && listeningStateRef.current === 'waiting') {
            safeStartRecognition();
          }
        }, 2000);
      };

      recognition.onend = () => {
        isRecognitionRunningRef.current = false;
        const currentState = listeningStateRef.current;

        if (stoppedForTtsRef.current) {
          return;
        }

        if (currentState === 'processing') {
          setTimeout(() => {
            if (listeningStateRef.current === 'waiting' && !isRecognitionRunningRef.current) {
              wakeWordDetectedRef.current = false;
              safeStartRecognition();
            }
          }, 1500);
          return;
        }

        setTimeout(() => {
          if (listeningStateRef.current === 'processing' || stoppedForTtsRef.current) {
            return;
          }
          if (isRecognitionRunningRef.current) {
            return;
          }
          const stateNow = listeningStateRef.current;
          // Continuous recognition fires onend often; do not exit command mode here or the next
          // utterance is ignored (wake/command ref mismatch).
          if (stateNow === 'command' && wakeWordDetectedRef.current) {
            safeStartRecognition();
            setTimeout(() => {
              if (!isRecognitionRunningRef.current) {
                safeStartRecognition();
              }
            }, 200);
            return;
          }
          if (wakeWordDetectedRef.current) {
            wakeWordDetectedRef.current = false;
            listeningStateRef.current = 'waiting';
            setListeningState('waiting');
            setStatus({ message: 'Say "Sonic" to activate', type: 'info' });
          }
          safeStartRecognition();
        }, 300);
      };

      recognitionRef.current = recognition;
      isInitializedRef.current = true;

      setTimeout(() => {
        safeStartRecognition();
      }, 500);
    } else {
      setStatus({ message: 'Speech recognition not available in this browser', type: 'error' });
    }

    return () => {
      safeStopRecognition();
    };
  }, [scheduleActivationListen]);

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

        <div className="tab-navigation">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            💬 Chat
          </button>
          <button
            className={`tab-btn ${activeTab === 'reminders' ? 'active' : ''}`}
            onClick={() => setActiveTab('reminders')}
          >
            📝 Reminders
          </button>
        </div>

        <div className="main-content">
          {activeTab === 'chat' && (
            <>
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
            </>
          )}

          {activeTab === 'reminders' && <Reminders />}
        </div>
      </div>
    </div>
  );
}

export default App;
