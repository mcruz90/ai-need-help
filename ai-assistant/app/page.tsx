'use client';

import { useState, useCallback, useEffect } from 'react';
import ChatInterface from './components/chat/ChatInterface';
import { NotionDisplay } from './components/notion/notionDisplay';
import Calendar from './components/calendar/Calendar';
import Sidebar from './components/Sidebar';
import { useChat } from './hooks/useChat';
import { setupVoiceRecognition } from './utils/voiceRecognition';
import './components/chat/ChatInterface.css';
import './components/codeblock/CodeBlock.css';

// This is the main page of the app; components are imported from other files and used to build the UI
export default function Home() {
  const { messages, handleNewMessage } = useChat();
  const [interimTranscript, setInterimTranscript] = useState('');
  const [inputMessage, setInputMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAsideOpen, setIsAsideOpen] = useState(false);
  const [asideContent, setAsideContent] = useState<'chat' | 'calendar'>('chat');

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

  const toggleAside = (content: 'chat' | 'calendar') => {
    if (isAsideOpen && asideContent === content) {
      setIsAsideOpen(false);
    } else {
      setIsAsideOpen(true);
      setAsideContent(content);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      <main className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
        <header className="bg-white shadow-sm">
          <div className="w-full px-4 py-3 flex justify-between items-center">
            <h1 className="text-2xl font-semibold">hi</h1>
            <div>
              <button
                onClick={() => toggleAside('chat')}
                className="px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all duration-300 mr-2"
              >
                {isAsideOpen && asideContent === 'chat' ? 'Close Chat' : 'Open Chat'}
              </button>
              <button
                onClick={() => toggleAside('calendar')}
                className="px-4 py-2 rounded-md bg-green-500 text-white hover:bg-green-600 transition-all duration-300"
              >
                {isAsideOpen && asideContent === 'calendar' ? 'Close Calendar' : 'Open Calendar'}
              </button>
            </div>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <section className="flex-1 overflow-hidden p-4">
            <NotionDisplay />
          </section>
          <aside className={`bg-white border-l overflow-hidden transition-all duration-300 ${
            isAsideOpen ? 'w-1/3' : 'w-0'
          }`}>
            {isAsideOpen && (
              <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto p-4">
                  {asideContent === 'chat' ? (
                    <ChatInterface
                      messages={messages}
                      onNewMessage={handleNewMessage}
                      interimTranscript={interimTranscript}
                      inputMessage={inputMessage}
                      setInputMessage={setInputMessage}
                      isListening={isListening}
                      toggleListening={toggleListening}
                    />
                  ) : (
                    <Calendar />
                  )}
                </div>
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}