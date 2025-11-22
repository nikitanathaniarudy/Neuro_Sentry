import React, { useEffect, useRef, useState } from "react";

type PromptPanelProps = {
  onPhraseStart?: () => void;
};

type Step = { label: string; duration: number; action?: () => void };

const steps: Step[] = [
  { label: "Neutral", duration: 3000 },
  { label: "Smile", duration: 3000 },
  { label: "Eyebrows", duration: 3000 },
  { label: "Say the phrase", duration: 4000 },
];

export const PromptPanel: React.FC<PromptPanelProps> = ({ onPhraseStart }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [running, setRunning] = useState(false);
  const timerRef = useRef<number>();

  useEffect(() => {
    if (!running) return;

    const current = steps[activeIndex];
    if (!current) return;

    if (current.label.startsWith("Say") && onPhraseStart) {
      onPhraseStart();
    }

    timerRef.current = window.setTimeout(() => {
      if (activeIndex + 1 < steps.length) {
        setActiveIndex((i) => i + 1);
      } else {
        setRunning(false);
      }
    }, current.duration);

    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [activeIndex, running, onPhraseStart]);

  const restart = () => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    setActiveIndex(0);
    setRunning(true);
  };

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Prompt Script</h3>
        <div className="row" style={{ alignItems: "center" }}>
          <button className="primary" onClick={restart} disabled={running}>
            {running ? "Running" : "Start"}
          </button>
          <button className="ghost" onClick={() => setRunning(false)} style={{ marginLeft: 8 }}>
            Stop
          </button>
        </div>
      </div>

      <div style={{ marginTop: 10 }}>
        {steps.map((step, idx) => (
          <div
            key={step.label}
            className="prompt-step"
            style={{
              border: idx === activeIndex && running ? "1px solid #4fc3f7" : "1px solid transparent",
            }}
          >
            <div>{idx + 1}. {step.label}</div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>{step.duration / 1000}s</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PromptPanel;
