import React, { useEffect, useRef } from 'react';
import './ReasoningDisplay.css';

function ReasoningDisplay({ reasoning, isProcessing }) {
  const stepsEndRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to latest step
    if (stepsEndRef.current) {
      stepsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [reasoning]);

  if (!reasoning || reasoning.length === 0) {
    if (!isProcessing) return null;
    return (
      <div className="reasoning-display">
        <div className="reasoning-header">
          <span className="reasoning-title">🤖 LLM Reasoning</span>
          <span className="reasoning-status">Processing...</span>
        </div>
        <div className="reasoning-steps">
          <div className="reasoning-step processing">
            <div className="step-icon">💭</div>
            <div className="step-content">Analyzing request...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="reasoning-display">
      <div className="reasoning-header">
        <span className="reasoning-title">🤖 LLM Reasoning</span>
        <span className="reasoning-status">{isProcessing ? 'Processing...' : 'Complete'}</span>
      </div>
      <div className="reasoning-steps">
        {reasoning.map((step, index) => {
          let stepType = 'default';
          let icon = '💭';
          
          // Determine step type based on content
          if (step.includes('Received') || step.includes('💭')) {
            stepType = 'default';
            icon = '💭';
          } else if (step.includes('Analyzing') || step.includes('Decided') || step.includes('Step') || step.includes('🤔')) {
            stepType = 'thinking';
            icon = '🤔';
          } else if (step.includes('Executing') || step.includes('Action:') || step.includes('🔧')) {
            stepType = 'action';
            icon = '🔧';
          } else if (step.includes('Result:') || step.includes('📊')) {
            stepType = 'result';
            icon = '📊';
          } else if (step.includes('Error') || step.includes('❌')) {
            stepType = 'error';
            icon = '❌';
          } else if (step.includes('completed') || step.includes('✅')) {
            stepType = 'success';
            icon = '✅';
          } else if (step.includes('Processing')) {
            stepType = 'processing';
            icon = '⚙️';
          }
          
          const isLastStep = index === reasoning.length - 1;
          
          return (
            <div 
              key={index} 
              ref={isLastStep ? stepsEndRef : null}
              className={`reasoning-step ${stepType} ${isProcessing && isLastStep ? 'active' : ''}`}
            >
              <div className="step-icon">{icon}</div>
              <div className="step-content">{step.replace(/^(🤔|🔧|📊|❌|💭|⚙️|✅)\s*/, '')}</div>
              {isProcessing && isLastStep && (
                <div className="step-loader"></div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ReasoningDisplay;

