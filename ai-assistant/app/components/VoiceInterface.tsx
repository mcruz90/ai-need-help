'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MicrophoneIcon } from '@heroicons/react/24/outline';

interface VoiceInterfaceProps {
  onNewMessage: (message: string) => Promise<void>;
  onInterimTranscript: (transcript: string) => void;
  onFinalTranscript: (transcript: string) => void;
}

const VoiceInterface: React.FC<VoiceInterfaceProps> = ({ onNewMessage, onInterimTranscript, onFinalTranscript }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      recognitionRef.current = new (window as any).webkitSpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onstart = () => {
        console.log('Speech recognition started');
        setIsListening(true);
      };

      recognitionRef.current.onerror = (event: any) => {
        if (event.error !== 'aborted') {
          console.error('Speech recognition error', event);
        }
      };

      recognitionRef.current.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
      };

      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        setTranscript(finalTranscript || interimTranscript);
        
        if (interimTranscript) {
          console.log('Interim transcript:', interimTranscript);
          onInterimTranscript(interimTranscript);
        }
        
        if (finalTranscript) {
          console.log('Final transcript:', finalTranscript);
          onFinalTranscript(finalTranscript);
          onNewMessage(finalTranscript);
        }
      };
    } else {
      console.log('Speech recognition not supported');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onNewMessage, onInterimTranscript, onFinalTranscript]);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
    }
  };

  return (
    <div className="mt-4">
      <button
        onClick={toggleListening}
        className={`p-2 rounded-full ${
          isListening ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
        } text-white`}
        aria-label={isListening ? 'Stop Listening' : 'Start Listening'}
      >
        <MicrophoneIcon className="h-6 w-6" />
      </button>
      <div className="mt-2">
        <p>Transcript: {transcript}</p>
      </div>
    </div>
  );
};

export default VoiceInterface;
