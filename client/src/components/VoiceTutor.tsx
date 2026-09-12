import React from "react";
import { motion, AnimatePresence } from "motion/react";

interface VoiceTutorProps {
  isOpen: boolean;
  onClose: () => void;
  status: string;
  isRecording: boolean;
  userBars: number[];
  aiLevel: number;
}

const VoiceTutor: React.FC<VoiceTutorProps> = ({ 
  isOpen, 
  onClose, 
  status, 
  isRecording, 
  userBars, 
  aiLevel 
}) => {
  
  const isAiSpeaking = aiLevel > 0.04;
  const isUserSpeaking = userBars.some((b) => b > 25);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="voice-modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35 }}
        >
          <div className="voice-modal-container">
            {/* Header / Close Button */}
            <div className="voice-modal-header">
              <div className="voice-brand">
                <span className="logo-icon">∑</span>
                <span>Prism Live Voice</span>
              </div>
              <button
                type="button"
                className="voice-close-btn"
                onClick={onClose}
                aria-label="Close voice tutor"
              >
                ✕
              </button>
            </div>

            {/* Center: Fluid AI Voice Orb */}
            <div className="voice-fluid-stage">
              <motion.div
                className="voice-fluid-glow"
                animate={{
                  scale: isAiSpeaking ? 1 + aiLevel * 0.9 : 1,
                  opacity: isAiSpeaking ? 0.85 : 0.45,
                }}
                transition={{ type: "spring", stiffness: 180, damping: 20 }}
              />

              <motion.div
                className="voice-fluid-core"
                animate={{
                  scale: isAiSpeaking ? 1 + aiLevel * 0.6 : [1, 1.05, 1],
                  rotate: isAiSpeaking ? [0, 90, 180, 270, 360] : 0,
                  borderRadius: isAiSpeaking
                    ? [
                        "60% 40% 30% 70% / 60% 30% 70% 40%",
                        "40% 60% 70% 30% / 50% 60% 30% 60%",
                        "60% 40% 30% 70% / 60% 30% 70% 40%",
                      ]
                    : "50%",
                }}
                transition={{
                  scale: { type: "spring", stiffness: 220, damping: 15 },
                  rotate: { duration: 8, repeat: Infinity, ease: "linear" },
                  borderRadius: { duration: 3, repeat: Infinity, ease: "easeInOut" },
                }}
              >
                <div className="voice-fluid-inner" />
              </motion.div>

              <div className="voice-status-pill">
                <span className={`status-indicator-dot ${isRecording ? "active" : ""}`} />
                <span>
                  {status === "Connecting..."
                    ? "Connecting..."
                    : isAiSpeaking
                    ? "AI is speaking"
                    : isUserSpeaking
                    ? "Listening to you"
                    : "Ready · Speak anytime"}
                </span>
              </div>
            </div>

            {/* Bottom: User Voice Equalizer Bars */}
            <div className="voice-user-container">
              <div className="voice-user-bars" aria-label="Microphone volume bars">
                {userBars.map((height, idx) => (
                  <motion.div
                    key={idx}
                    className="voice-bar"
                    animate={{ height: `${height}px` }}
                    transition={{ type: "spring", stiffness: 450, damping: 25 }}
                  />
                ))}
              </div>
              <span className="voice-user-label">Your Voice</span>

              <div className="voice-actions">
                <button type="button" className="voice-end-btn" onClick={onClose}>
                  End Call
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default VoiceTutor;