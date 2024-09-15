'use client';

import { useState, useCallback, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import { NotionDisplay } from './components/notion/notionDisplay';
import Calendar from './components/calendar/Calendar';
import Sidebar from './components/Sidebar';
import { useChat } from './hooks/useChat';
import { setupVoiceRecognition } from './utils/voiceRecognition';
import './components/ChatInterface.css';
import './components/CodeBlock.css';

// This is the main page of the app; components are imported from other files and used to build the UI
export default function Home() {
  const { messages, handleNewMessage } = useChat();
  const [interimTranscript, setInterimTranscript] = useState('');
  const [inputMessage, setInputMessage] = useState('');
  const [isListening, setIsListening] = useState(false);

  // Interim transcript is the partial transcript as the user is speaking
  const handleInterimTranscript = useCallback((transcript: string) => {
    setInterimTranscript(transcript);
  }, []);

  // Final transcript is the full transcript after the user is done speaking
  const handleFinalTranscript = useCallback((transcript: string) => {
    const finalMessage = transcript.trim();
    setInputMessage(''); 
    setInterimTranscript('');
    if (finalMessage) {
      handleNewMessage(finalMessage); 
    }
  }, [handleNewMessage]);

  const [voiceRecognition, setVoiceRecognition] = useState<any>(null);

  // Setup voice recognition
  useEffect(() => {
    const recognition = setupVoiceRecognition(handleInterimTranscript, handleFinalTranscript);
    setVoiceRecognition(recognition);
    console.log('Voice recognition setup:', recognition);
  }, [handleInterimTranscript, handleFinalTranscript]);

  // Toggle listening to start and stop voice recognition
  const toggleListening = useCallback(() => {
    if (isListening) {
      console.log('Stopping voice recognition');
      voiceRecognition?.stop();
      setIsListening(false);
    } else {
      console.log('Starting voice recognition');
      voiceRecognition?.start();
      setIsListening(true);
    }
  }, [isListening, voiceRecognition]);

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-2 lg:px-4 flex flex-row">
            <h1 className="text-2xl font-semibold">hi</h1>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <section className="w-2/3 overflow-hidden p-4 flex">
            <div className="w-2/3 pr-2 h-full overflow-hidden">
              <NotionDisplay />
            </div>
            <div className="w-1/3 pl-2 h-full overflow-hidden">
              <Calendar />
            </div>
          </section>
          <aside className="w-1/3 bg-white p-4 border-l overflow-y-auto">
            <ChatInterface
              messages={messages}
              onNewMessage={handleNewMessage}
              interimTranscript={interimTranscript}
              inputMessage={inputMessage}
              setInputMessage={setInputMessage}
              isListening={isListening}
              toggleListening={toggleListening}
            />
          </aside>
        </div>
      </main>
    </div>
  );
}