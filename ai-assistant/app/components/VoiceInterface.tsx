'use client';

import React, { useState, useEffect, useCallback } from 'react';

interface VoiceInterfaceProps {
  onNewMessage: (message: string) => Promise<void>;
  onInterimTranscript: (transcript: string) => void;
  onFinalTranscript: (transcript: string) => void;  // Add this new prop
}

declare global {
  interface Window {
    webkitSpeechRecognition: any;
  }
}

const VoiceInterface: React.FC<VoiceInterfaceProps> = ({ onNewMessage, onInterimTranscript, onFinalTranscript }) => {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');

  const startListening = useCallback(() => {
    if (recognition) {
      recognition.start();
      setIsListening(true);
    }
  }, [recognition]);

  const stopListening = useCallback(() => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  }, [recognition]);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const recognitionInstance = new window.webkitSpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;

      recognitionInstance.onresult = (event: any) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        setInterimTranscript(interim);
        onInterimTranscript(interim);
        if (final) {
          setFinalTranscript(prev => prev + ' ' + final.trim());
          onFinalTranscript(final.trim());  // Call this new function with the final transcript
        }
      };

      recognitionInstance.onend = () => {
        if (isListening) {
          recognitionInstance.start();
        } else {
          setIsListening(false);
        }
      };

      setRecognition(recognitionInstance);
    }

    return () => {
      if (recognition) {
        recognition.stop();
      }
    };
  }, [onInterimTranscript, onFinalTranscript, isListening]);

  useEffect(() => {
    if (finalTranscript.trim()) {
      onNewMessage(finalTranscript.trim());
      setFinalTranscript('');
    }
  }, [finalTranscript, onNewMessage]);

  return (
    <div className="mt-4">
      <button
        onClick={isListening ? stopListening : startListening}
        className={`px-4 py-2 rounded ${
          isListening ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
        } text-white font-bold`}
      >
        {isListening ? 'Stop Listening' : 'Start Listening'}
      </button>
    </div>
  );
};

export default VoiceInterface;

